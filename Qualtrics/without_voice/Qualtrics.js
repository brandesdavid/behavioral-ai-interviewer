Qualtrics.SurveyEngine.addOnload(function () {

	////////////////////////////////////////////////////////////////
	// Key embedded data from the Qualtrics survey flow setup    ///
	////////////////////////////////////////////////////////////////
	var userID = Qualtrics.SurveyEngine.getEmbeddedData('user_id');
	var interviewID = Qualtrics.SurveyEngine.getEmbeddedData('interview_id');
    var endpoint = Qualtrics.SurveyEngine.getEmbeddedData('interview_endpoint');

	////////////////////////////////
    // Key input and output elements
	////////////////////////////////
    var chatArea = document.getElementById("chatArea");
    var submitButton = document.getElementById("submitButton");
    var inputField = document.getElementById("inputBox");

	///////////////////////////////////////////
	/// ADD NEW MESSAGES WITH DANCING DOTS ////
	///////////////////////////////////////////

    function appendChatbotMessage(message, chatArea, status) {
        var messageContent = document.createElement('div');
        messageContent.style.cssText = "word-wrap: break-word; width: 80%; border: 1px solid #F6F6F6; border-radius: 5px; padding: 5px; margin-bottom: 10px; background-color: #F6F6F6; display: block; margin-right: auto; font-size: 18px; line-height: 1.5;";

        if (status === "waiting") {
            messageContent.innerHTML = `
            <div>
            <div id="wave" style="position:relative; vertical-align: center; text-align:left;">
            <span class="dot" style="display:inline-block; width:12px; height:6px; border-radius:50%; margin-right:3px; background:#303131; animation: wave 1.3s linear infinite;"></span>
            <span class="dot" style="display:inline-block; width:12px; height:6px; border-radius:50%; margin-right:3px; background:#303131; animation: wave 1.3s linear infinite; animation-delay: -1.1s;"></span>
            <span class="dot" style="display:inline-block; width:12px; height:6px; border-radius:50%; margin-right:3px; background:#303131; animation: wave 1.3s linear infinite; animation-delay: -0.9s;"></span>
            </div><style>@keyframes wave {0%, 60%, 100% {transform: initial;} 30% {transform: translateY(-7px);}}</style></div>`;
            messageContent.id = "dancingDots";
        } else if (status === "response") {
            var existingDots = document.getElementById("dancingDots");
            if (existingDots) {
                existingDots.innerText = message.trim();
                existingDots.removeAttribute('id');
                chatArea.scrollTop = chatArea.scrollHeight;
                return;
            } else {
                messageContent.innerText = message.trim();
            }
        }
        chatArea.appendChild(messageContent);
        chatArea.scrollTop = chatArea.scrollHeight;
    }

	///////////////////////////////////////////
	/// DAG VALIDATION UI /////////////////////
	///////////////////////////////////////////

    function showDagValidation(dagSvg, validationQuestion) {
        // Disable normal input while awaiting DAG feedback
        submitButton.disabled = true;
        submitButton.style.backgroundColor = '#ccc';
        inputField.disabled = true;

        // Remove existing dancing dots if any
        var existingDots = document.getElementById("dancingDots");
        if (existingDots) existingDots.remove();

        // DAG container
        var dagContainer = document.createElement('div');
        dagContainer.style.cssText = "width: 90%; margin-bottom: 10px; margin-right: auto;";

        // SVG box
        var svgBox = document.createElement('div');
        svgBox.style.cssText = "overflow-x: auto; border: 1px solid #d0d7e3; border-radius: 6px; padding: 8px; background: #f8faff; margin-bottom: 10px;";
        svgBox.innerHTML = dagSvg;
        dagContainer.appendChild(svgBox);

        // Validation question text
        var questionEl = document.createElement('div');
        questionEl.style.cssText = "font-size: 18px; line-height: 1.5; margin-bottom: 10px; color: #1e3a5f; font-weight: 500;";
        questionEl.innerText = validationQuestion;
        dagContainer.appendChild(questionEl);

        // Yes / No buttons
        var btnRow = document.createElement('div');
        btnRow.style.cssText = "display: flex; gap: 10px; margin-bottom: 10px;";

        var yesBtn = document.createElement('button');
        yesBtn.innerText = "Ja";
        yesBtn.style.cssText = "padding: 8px 28px; font-size: 16px; background: #2563a8; color: white; border: none; border-radius: 5px; cursor: pointer;";

        var noBtn = document.createElement('button');
        noBtn.innerText = "Nein";
        noBtn.style.cssText = "padding: 8px 28px; font-size: 16px; background: #e5e7eb; color: #1e3a5f; border: none; border-radius: 5px; cursor: pointer;";

        btnRow.appendChild(yesBtn);
        btnRow.appendChild(noBtn);
        dagContainer.appendChild(btnRow);

        // Correction area (hidden initially)
        var correctionArea = document.createElement('div');
        correctionArea.style.cssText = "display: none;";
        correctionArea.innerHTML = `
            <textarea id="dagCorrectionText" placeholder="Bitte beschreiben Sie kurz, was nicht stimmt..."
                style="width:100%; height:80px; font-size:16px; border:1px solid #ccc; border-radius:5px; padding:6px; box-sizing:border-box; resize:vertical;"></textarea>
            <button id="dagCorrectionSubmit" style="margin-top:6px; padding:8px 20px; font-size:16px; background:#2563a8; color:white; border:none; border-radius:5px; cursor:pointer;">Absenden</button>
        `;
        dagContainer.appendChild(correctionArea);

        chatArea.appendChild(dagContainer);
        chatArea.scrollTop = chatArea.scrollHeight;

        // Yes handler
        yesBtn.addEventListener('click', function () {
            dagContainer.remove();
            sendDagFeedback('__DAG_ACCEPTED__', 'Ja');
        });

        // No handler — show correction box
        noBtn.addEventListener('click', function () {
            correctionArea.style.display = 'block';
            yesBtn.disabled = true;
            noBtn.disabled = true;
            chatArea.scrollTop = chatArea.scrollHeight;
        });

        // Correction submit handler
        correctionArea.querySelector('#dagCorrectionSubmit').addEventListener('click', function () {
            var correctionText = correctionArea.querySelector('#dagCorrectionText').value.trim();
            if (!correctionText) return;
            dagContainer.remove();
            sendDagFeedback('__DAG_REJECTED__::' + correctionText, 'Nein – ' + correctionText);
        });
    }

    function sendDagFeedback(sentinelMessage, displayLabel) {
        // Show user's choice in chat
        var userBubble = document.createElement('div');
        userBubble.style.cssText = "display: inline-block; max-width: 80%; border: 1px solid #ddd; border-radius: 5px; padding: 5px; margin-bottom: 10px; background-color: #ddd; word-wrap: break-word; font-size: 18px; line-height: 1.5;";
        userBubble.innerText = displayLabel;
        chatArea.appendChild(userBubble);

        appendChatbotMessage("", chatArea, "waiting");
        chatArea.scrollTop = chatArea.scrollHeight;

        jQuery.ajax({
            url: endpoint,
            timeout: 60000,
            type: "POST",
            data: JSON.stringify({
                route: "next",
                payload: {
                    user_message: sentinelMessage,
                    session_id: userID,
                    interview_id: interviewID
                }
            }),
            contentType: "application/json",
            dataType: "json",
            success: function (data) {
                handleServerResponse(data);
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.error("Error:", errorThrown);
                appendChatbotMessage("Es gab einen technischen Fehler. Bitte versuchen Sie es erneut.", chatArea, "response");
                restoreInput();
            }
        });
    }

    function restoreInput() {
        submitButton.disabled = false;
        submitButton.style.backgroundColor = '#007BFF';
        submitButton.innerText = "Submit response";
        inputField.disabled = false;
    }

    function handleServerResponse(data) {
        var nextQuestion = data.message.trim();
        var dagSvg = data.dag_svg || null;

        // Check for end of interview
        if (nextQuestion.indexOf("---END---") !== -1) {
            nextQuestion = nextQuestion.replace("---END---", "").trim();
            appendChatbotMessage(nextQuestion, chatArea, "response");
            submitButton.disabled = true;
            submitButton.innerText = "End of interview";
            inputField.disabled = true;
            return;
        }

        if (dagSvg) {
            // Remove dancing dots manually before showing DAG UI
            var existingDots = document.getElementById("dancingDots");
            if (existingDots) existingDots.remove();
            showDagValidation(dagSvg, nextQuestion);
        } else {
            appendChatbotMessage(nextQuestion, chatArea, "response");
            restoreInput();
        }
    }

	////////////////////////////////////////////
    // GET THE FIRST QUESTION FROM THE SERVER //
	////////////////////////////////////////////
    jQuery.ajax({
        url: endpoint,
        timeout: 60000,
        type: "POST",
        data: JSON.stringify({
            route: "next",
            payload: {
                user_message: "",
                session_id: userID,
                interview_id: interviewID
            }
        }),
        contentType: "application/json",
        dataType: "json",
        success: function (data) {
            var question = data.message.trim();
            appendChatbotMessage(question, chatArea, "response");
            Qualtrics.SurveyEngine.setEmbeddedData('first_question', question);
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.error("Error:", errorThrown);
            appendChatbotMessage("There was a technical error. Please refresh or proceed in the survey.", chatArea, "response");
        }
    });


	////////////////////////////////////////////////////////////
    // Prevent copy, cut, and paste in chatArea and inputField /
	////////////////////////////////////////////////////////////
    ["copy", "cut", "paste"].forEach(function (eventType) {
        [chatArea, inputField].forEach(function (element) {
            element.addEventListener(eventType, function (event) {
                event.preventDefault();
            });
        });
    });


	////////////////////////////////////////////////////////////
    // GENERATE THE NEXT QUESTION ON SUBMIT BUTTON CLICK ///////
	////////////////////////////////////////////////////////////
    submitButton.addEventListener("click", function () {
        var userMessage = inputField.value.trim();
        if (userMessage) {
            inputField.value = "";

            submitButton.disabled = true;
            submitButton.style.backgroundColor = '#ccc';
            submitButton.innerText = "Waiting for reply...";

            var messageContent = document.createElement('div');
            messageContent.style.cssText = "display: inline-block; max-width: 80%; border: 1px solid #ddd; border-radius: 5px; padding: 5px; margin-bottom: 10px; background-color: #ddd; word-wrap: break-word; white-space: pre-wrap; box-sizing: border-box; font-size: 18px; text-align: left; line-height: 1.5;";
            messageContent.innerText = userMessage;
            chatArea.appendChild(messageContent);
            chatArea.scrollTop = chatArea.scrollHeight;

            appendChatbotMessage("", chatArea, "waiting");

            jQuery.ajax({
                url: endpoint,
                timeout: 60000,
                type: "POST",
                data: JSON.stringify({
					route: "next",
					payload: {
						user_message: userMessage,
						session_id: userID,
						interview_id: interviewID
					}
                }),
                contentType: "application/json",
                dataType: "json",
                success: function (data) {
                    handleServerResponse(data);
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    console.error("Error:", errorThrown);
                    appendChatbotMessage("There was a technical error. Please try again.", chatArea, "response");
                    restoreInput();
                }
            });
        }
    });

});

Qualtrics.SurveyEngine.addOnReady(function () {
	/*Place your JavaScript here to run when the page is fully displayed*/

});

Qualtrics.SurveyEngine.addOnUnload(function () {
	/*Place your JavaScript here to run when the page is unloaded*/

});
