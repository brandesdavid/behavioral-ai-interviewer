import logging
from parameters import INTERVIEW_PARAMETERS
from core.manager import InterviewManager
from core.agent import LLMAgent
from core.providers import get_provider
from core.svg_generator import dag_to_svg

DAG_VALIDATION_QUESTION = (
    "Passt dieser Graph genau zu Ihrem mentalen Bild? "
    "Bitte antworten Sie mit Ja oder Nein. "
    "Falls Nein, können Sie kurz erklären, was nicht stimmt."
)


def connect_to_database():
    """ Instantiate file-based database. """
    from database.file import FileWriter
    return FileWriter()


db = connect_to_database()
agent = LLMAgent(get_provider())


def load_interview_session(session_id: str) -> dict:
    """ Return interview session history to user. """
    return db.load_remote_session(session_id)


def delete_interview_session(session_id: str):
    """ Delete existing interview saved to database. """
    db.delete_remote_session(session_id)


def resume_interview_session(session_id: str, interview_id: str, user_message: str) -> InterviewManager:
    """ Return InterviewManager object of existing session. """
    interview = InterviewManager(db, session_id)
    interview.resume_session(INTERVIEW_PARAMETERS[interview_id])
    logging.info("Generating next question for session '{}', user message '{}'".format(
        session_id,
        user_message
    ))
    return interview


def begin_interview_session(session_id: str, interview_id: str) -> dict:
    """ Return response with starting question of new interview session. """
    if not INTERVIEW_PARAMETERS.get(interview_id):
        raise ValueError(
            f"Invalid interview parameters '{interview_id}' specified!")
    parameters = INTERVIEW_PARAMETERS[interview_id]
    interview = InterviewManager(db, session_id)
    interview.begin_session(parameters)
    message = parameters['first_question']
    interview.add_chat_to_session(message, type='question')
    logging.info("Beginning {} interview session '{}' with prompt '{}'".format(
        interview_id,
        session_id,
        message
    ))
    return {'session_id': session_id, 'interview_id': interview_id, 'message': message}


def retrieve_sessions(sessions: list = None) -> dict:
    """ Return specified or all existing interview sessions. """
    return db.retrieve_sessions(sessions)


def transcribe(audio: str) -> dict:
    """ Return audio file transcription using OpenAI Whisper API """
    logging.critical(f"Audio is: {type(audio)}...")
    transcription = agent.transcribe(audio)
    logging.info(f"Returning transcription text: '{transcription}'")
    return {'transcription': transcription}


def next_question(session_id: str, interview_id: str, user_message: str = None) -> dict:
    """
    Process user message and generate response by the AI-interviewer.

    Args:
        session_id: (str) unique interview session ID
        user_message: (str) interviewee response
        interview_id: (str) containing interview guidelines index
    Returns:
        response: (dict) containing `message` from interviewer
    """

    # Resume if interview has started, otherwise begin (new) session
    try:
        interview = resume_interview_session(
            session_id, interview_id, user_message)
        parameters = interview.parameters
    except AssertionError:
        return begin_interview_session(session_id, interview_id)

    # Exit condition: this interview has been previously ended
    if interview.is_terminated():
        return {'session_id': session_id, 'message': parameters['termination_message']}

    # Handle DAG validation feedback (sentinel-prefixed messages from frontend)
    if interview.is_awaiting_dag_feedback():
        msg = user_message or ''
        if msg.startswith('__DAG_ACCEPTED__'):
            interview.resolve_dag_feedback(accepted=True)
        elif msg.startswith('__DAG_REJECTED__::'):
            correction = msg[len('__DAG_REJECTED__::'):]
            interview.resolve_dag_feedback(accepted=False, correction=correction)
        else:
            # Still waiting — re-ask validation question
            interview.update_session()
            return {'session_id': session_id, 'message': DAG_VALIDATION_QUESTION}

        pending_question = interview.consume_pending_question()
        interview.add_chat_to_session(pending_question, type='question')
        return {'session_id': session_id, 'message': pending_question}

    # Provide interview guidelines to LLM agent
    agent.load_parameters(parameters)

    # Optional: Moderate interviewee responses, e.g. flagging off-topic or harmful messages
    if parameters.get('moderate_answers') and parameters.get('moderator'):
        on_topic = agent.review_answer(user_message, interview.get_history())
        if not on_topic:
            interview.flag_risk(user_message)

        # Terminate if the conversation has been flagged too often
        if interview.flagged_too_often():
            interview.update_session()
            return {'session_id': session_id, 'message': parameters['flagged_message']}

        # If user message does not fit the interview context, give another chance
        if not on_topic:  # but not flagged too often...
            interview.update_session()
            return {'session_id': session_id, 'message': parameters['off_topic_message']}

    """
    UPDATE INTERVIEW WITH NEW USER MESSAGE
    Note this happens *after* security checks such that
    flagged messages are *not* added to interview history.
    """
    interview.add_chat_to_session(user_message, type="answer")

    ##### CONTINUE INTERVIEW BASED ON WORKFLOW #####

    # Current topic guide
    num_topics = len(parameters['interview_plan'])
    current_topic_idx = interview.get_current_topic()
    on_last_topic = current_topic_idx == num_topics
    logging.info(f"On topic {current_topic_idx}/{num_topics}...")

    # Current question within topic guide
    current_question_idx = interview.get_current_topic_question()
    num_questions = parameters['interview_plan'][current_topic_idx-1]['length']
    on_last_question = current_question_idx >= num_questions
    logging.info(f"On question {current_question_idx}/{num_questions}...")

    # Continue in workflow
    if on_last_topic and on_last_question:
        # Close interview with pre-determined closing questions
        next_question = interview.get_final_question()
        interview.update_closing()
        if not next_question:
            # Exit condition: have already produced last "final" question
            interview.terminate()
            interview.update_session()
            return {'session_id': session_id, 'message': parameters['end_of_interview_message']}

    elif on_last_question:
        # Extract causal DAG for the completed topic if configured
        dag = {}
        dag_svg = ''
        if parameters.get('dag'):
            current_topic = parameters['interview_plan'][current_topic_idx - 1]['topic']
            dag = agent.extract_dag(
                current_topic, current_topic_idx, interview.get_history())
            dag_svg = dag_to_svg(dag)
            interview.add_topic_dag(dag, current_topic, svg=dag_svg)
        # Transition to *next* topic...
        transition_q, summary = agent.transition_topic(interview.get_history())
        interview.update_transition(summary)

        # If DAG was extracted, pause for user validation before continuing
        if dag and dag_svg:
            interview.set_dag_pending(transition_q)
            interview.add_chat_to_session(DAG_VALIDATION_QUESTION, type='question')
            return {
                'session_id': session_id,
                'message': DAG_VALIDATION_QUESTION,
                'dag_svg': dag_svg,
                'dag': dag,
            }

        next_question = transition_q

    else:
        # Proceed *within* topic...
        dag = {}
        next_question = agent.probe_within_topic(interview.get_history())
        interview.update_probe()

    # Update interview with new output
    logging.info(f"Interviewer responded: '{next_question}'")
    interview.add_chat_to_session(next_question, type="question")

    # Optional: Check if next question is flagged by OpenAI's moderation endpoint
    if parameters.get('moderate_questions'):
        flagged_question = agent.review_question(next_question)
        if flagged_question:
            interview.terminate(reason="question_flagged")
            interview.update_session()
            return {'session_id': session_id, 'message': parameters['end_of_interview_message']}

    return {'session_id': session_id, 'message': next_question}
