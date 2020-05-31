// main.js

'use strict';


const pushButton = document.querySelector('.js-push-btn');

let isSubscribed = false;
let swRegistration = null;

function urlB64ToUint8Array(base64String) {
	const padding = '='.repeat((4 - base64String.length % 4) % 4);
	const base64 = (base64String + padding)
		.replace(/\-/g, '+')
		.replace(/_/g, '/');

	const rawData = window.atob(base64);
	const outputArray = new Uint8Array(rawData.length);

	for (let i = 0; i < rawData.length; ++i) {
		outputArray[i] = rawData.charCodeAt(i);
	}
	return outputArray;
}

function updateBtn() {
	if (Notification.permission === 'denied') {
		pushButton.textContent = 'Push Messaging Blocked.';
		pushButton.disabled = true;
		updateSubscriptionOnServer(null);
		return;
	}

	if (isSubscribed) {
		pushButton.textContent = 'Disable Push Messaging';
	} else {
		pushButton.textContent = 'Enable Push Messaging';
	}

	pushButton.disabled = false;
}

function updateSubscriptionOnServer(subscription) {
	const subscriptionJson = document.querySelector('.js-subscription-json');
	const subscriptionDetails =
		document.querySelector('.js-subscription-details');

	if (subscription) {
		subscriptionJson.textContent = JSON.stringify(subscription);
		subscriptionDetails.classList.remove('is-invisible');
	} else {
		subscriptionDetails.classList.add('is-invisible');
	}
}

function subscribeUser() {
	const applicationServerPublicKey = localStorage.getItem('applicationServerPublicKey');
	const applicationServerKey = urlB64ToUint8Array(applicationServerPublicKey);
	swRegistration.pushManager.subscribe({
		userVisibleOnly: true,
		applicationServerKey: applicationServerKey
	})
		.then(function (subscription) {
			fetch(`/sub`);
			$.ajax({
				type: "POST",
				url: "/subscribe/",
				contentType: 'application/json; charset=utf-8',
				dataType: 'json',
				data: JSON.stringify({ 'sub_token': subscription }),
				success: function (data) {
					
				},
				error: function (jqXhr, textStatus, errorThrown) {
				}
			});
			updateSubscriptionOnServer(subscription);
			localStorage.setItem('sub_token', JSON.stringify(subscription));
			isSubscribed = true;
			location.reload();
			updateBtn();
		})
		
		.catch(function (err) {
			updateBtn();
		});

}

function unsubscribeUser() {
	fetch(`/unsubscribe`);
	swRegistration.pushManager.getSubscription()
		.then(function (subscription) {
			if (subscription) {
				return subscription.unsubscribe();
			}
		})
		.catch(function (error) {
		})
		.then(function () {
			updateSubscriptionOnServer(null);

			isSubscribed = false;

			updateBtn();
		});
}

function initializeUI() {
	pushButton.addEventListener('click', function () {
		pushButton.disabled = true;
		if (isSubscribed) {
			unsubscribeUser();
		} else {
			subscribeUser();
		}
	});


	swRegistration.pushManager.getSubscription()
		.then(function (subscription) {
			isSubscribed = !(subscription === null);

			updateSubscriptionOnServer(subscription);

			if (isSubscribed) {
			} else {
			}

			updateBtn();
		});
}

if ('serviceWorker' in navigator && 'PushManager' in window) {
	navigator.serviceWorker.register("/static/sw.js?v=47")
		.then(function (swReg) {
			swRegistration = swReg;
			initializeUI();
		})
		.catch(function (error) {
		});
} else {
	pushButton.textContent = 'Push Not Supported';
}

$(document).ready(function () {
	$.ajax({
		type: "GET",
		url: '/subscription/',
		success: function (response) {
			localStorage.setItem('applicationServerPublicKey', response.public_key);
		}
	})
});


const channel = new BroadcastChannel('sw-messages');
channel.addEventListener('message', event => {
	modal.style.display = "none";
	fetch(`/complete?id=${pushed_task}`).then(response => (
		pushed_task = false,
		location.reload()
	));

});



var taskArea = document.getElementById('taskArea');

function setTime(pos, elID = null) {
	var num = pos;
	var hours = (num / 60);
	var rhours = Math.floor(hours);
	var minutes = (hours - rhours) * 60;
	var rminutes = Math.round(minutes);
	if (rhours < 10 && rminutes < 10) {
		if (elID) {
			document.getElementById(elID).value = `0${rhours.toString()}:0${rminutes.toString()}`;
		}
		else {
			return `0${rhours.toString()}:0${rminutes.toString()}`
		}
	}
	else if (rhours > 9 && rminutes < 10) {
		if (elID) {
			document.getElementById(elID).value = `${rhours.toString()}:0${rminutes.toString()}`;
		}
		else {
			return `${rhours.toString()}:0${rminutes.toString()}`
		}
	}
	else if (rhours < 10 && rminutes > 9) {
		if (elID) {
			document.getElementById(elID).value = `0${rhours.toString()}:${rminutes.toString()}`;
		}
		else {
			return `0${rhours.toString()}:${rminutes.toString()}`
		}
	}
	else {
		if (elID) {
			document.getElementById(elID).value = `${rhours.toString()}:${rminutes.toString()}`;
		}
		else {
			return `${rhours.toString()}:${rminutes.toString()}`;
		}
	}
};


if (document.getElementById("timeline")) {
	var timeline = document.getElementById("timeline");
	timeline.style.left = '0px';
	var nextDate = new Date();
	nextDate.setHours(24);
	nextDate.setMinutes(0);
	var now = 1440 - (((nextDate - new Date()) / 60) / 1000);
	timeline.style.top = now;

	setInterval(timeLine, 60000);
	var pushed_task = false;

	function timeLine() {
		var nextDate = new Date();
		nextDate.setHours(24);
		nextDate.setMinutes(0);
		var now = 1440 - (((nextDate - new Date()) / 60) / 1000);
		timeline.style.top = now;

		if (taskEndTimes.includes(now)) {

			var unlock = `${now}`
			modal.style.display = "block";
			fetch(`/check?id=${taskEndTimeIDs[unlock][0]}`).then(response => (
				pushed_task = taskEndTimeIDs[unlock][0]
			));
			$('#modal-title').html(
				`${taskEndTimeIDs[unlock][1]}`
			);
			$('#button').html(
				`<button class="btn btn-outline-success flashing effect" style="display: inline-block"> I have done this</button>`
			);
			$('#button2').html(
				`<button class="btn btn-outline-danger flashing effect" style="display: inline-block"> I have not done this</button>`
			);
			var button = document.getElementsByClassName("flashing effect")[0];
			button.onclick = function () {
				modal.style.display = "none";
				fetch(`/complete?id=${taskEndTimeIDs[unlock][0]}`).then(response => (
					location.reload()
				));

			}

			button2.onclick = function () {
				modal.style.display = "none";

			}
		}
	};
};

var taskEndTimeIDs = {};
var taskEndTimes = [];

function Rectangle(ypos, height, task, id, color, frequency) {
	var newTask = document.createElement("DIV");
	newTask.innerHTML = `<div class='taskText'>${task} from ${setTime(ypos)} to ${setTime(ypos + height)}</div>`;
	newTask.setAttribute('id', id);
	newTask.setAttribute('class', "ui-widget-content draggable");
	newTask.style.left = '0px';
	newTask.style.top = `${ypos}px`;
	newTask.style.height = `${height}px`;
	newTask.style.width = '100%';
	newTask.style.backgroundColor = hexToRgbA(`#${color}`)
	taskArea.appendChild(newTask);
	taskEndTimeIDs[`${ypos + height}`] = [id, task];
	taskEndTimes.push(ypos + height);
	newTask.onclick = function (e) {
		document.addEventListener("click", handler, true);

		editTaskModal.style.display = "block";
		var top = parseInt(e.target.style.top);
		setTime(top, "editStart");
		setTime(top + parseInt(e.target.style.height), "end");
		e.stopPropagation();
		document.getElementById("taskEdit").value = task
		document.getElementById("editColor").value = color;
		document.getElementById('editID').value = id;
		if (frequency == "None") {
			document.getElementById('editFrequency').value = '';
			document.getElementById('editSingleEvent').style.visibility = 'hidden';
		}
		else {
			document.getElementById('editFrequency').value = frequency;
		};

	}



};

var leftCol = document.getElementById("colLeft");
var toAdd = document.createDocumentFragment();
for (var i = 0; i < 1440; i++) {
	if (i == 0 || i % 60 == 0) {

		var newHour = document.createElement("P");
		if (i == 0) {
			newHour.innerHTML = i + ":00";
		}
		else if (i % 60 == 0) {
			newHour.innerHTML = (i / 60) + ":00";
		}
		newHour.setAttribute('class', "timeHour");
		newHour.style.position = "absolute";
		newHour.setAttribute('id', `a${i}`);
		newHour.style.left = '50%';
		newHour.style.top = `${i}px`;
		toAdd.appendChild(newHour);
	}
}
leftCol.appendChild(toAdd);


var taskModal = document.getElementById("myTaskModal");
var editTaskModal = document.getElementById("myEditTaskModal");

var spanTask = document.getElementsByClassName("task-close")[0];
var spanEditTask = document.getElementsByClassName("task-close")[1];


taskArea.onclick = function (event) {
	document.addEventListener("click", handler, true);
	taskModal.style.display = "block";
	if (event.offsetY < 60) {
		document.getElementById("start").value = `00:00`;
	}
	else if (event.offsetY < 600) {
		document.getElementById("start").value = `0${String(event.offsetY / 60).charAt(0)}:00`;
	}
	else {
		document.getElementById("start").value = `${String(event.offsetY / 60).substring(0, 2)}:00`;
	}

}


spanTask.onclick = function () {
	taskModal.style.display = "none";
}

spanEditTask.onclick = function () {
	editTaskModal.style.display = "none";
}

function insertCert() {
	$.ajaxSetup({
		beforeSend: function (xhr, settings) {
			if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
				xhr.setRequestHeader("X-CSRFToken", "{{ form.csrf_token._value() }}")
			}
		}
	})
}

$(document).ready(function () {
	$('#editTasks').submit(function (e) {
		editTaskModal.style.display = "none";
		$.ajax({
			type: "POST",
			url: '/edit_task/',
			data: $('#editTasks').serialize(),
			success: function (data) {
				window.location.href = `index/ph?r=#${data.id}`
				window.location.reload(true)

			}
		});
		e.preventDefault();
	});
	insertCert()
});



$(document).ready(function () {
	$('#tasks').submit(function (e) {
		taskModal.style.display = "none";
		$.ajax({
			type: "POST",
			url: '/new_task/',
			data: $('#tasks').serialize(),
			success: function (data) {
				new Rectangle(data.minutes, data.height, data.task, data.id, data.color, data.frequency);
				location.reload()
			}
		});
		e.preventDefault();
	});
	insertCert()
});

var noClick = false;
document.addEventListener("click", handler, true);
function handler(e) {
	if (noClick == true) {
		e.stopPropagation();
		e.preventDefault();
	}
	else {
		document.removeEventListener('click', handler)
	}
}


$(function () {


	$(".draggable").draggable(
		{
			start: function (event, ui) {
				noClick = true;
			},
			axis: "y",
			containment: "parent",
			grid: [50, 10],
			stop: function (event, ui) {
				var old_end = ui.originalPosition.top + parseInt(event.target.style.height);
				if (parseInt(event.target.style.top) + parseInt(event.target.style.height) != old_end) {
					taskEndTimeIDs[`${parseInt(event.target.style.top) + parseInt(event.target.style.height)}`] = taskEndTimeIDs[`${old_end}`];
					delete taskEndTimeIDs[`${old_end}`];
				}
				var index = taskEndTimes.indexOf(old_end);
				taskEndTimes[index] = parseInt(event.target.style.top) + parseInt(event.target.style.height)
				$.ajax({
					type: "POST",
					contentType: "application/json;charset=utf-8",
					url: '/update_task/',
					data: JSON.stringify({ 'id': event.target.id, 'height': event.target.style.height, 'top': event.target.style.top }), // serializes the form's elements.
					success: function (data) {
						event.target.querySelector(".taskText").innerHTML = `${data.task} from ${setTime(parseInt(event.target.style.top))} to ${setTime(parseInt(event.target.style.top) + parseInt(event.target.style.height))}`;

						taskModal.style.display = "none";
						editTaskModal.style.display = "none";
						noClick = false;

					}
				});
			}
		}
	).resizable({
		start: function (event, ui) {
			noClick = true;
		},

		containment: "parent",

		handles: 'n, s',
		stop: function (event, ui) {
			var old_end = ui.originalPosition.top + ui.originalSize.height + 2;
			if (parseInt(event.target.style.top) + parseInt(event.target.style.height) != old_end) {
				taskEndTimeIDs[`${parseInt(event.target.style.top) + parseInt(event.target.style.height) + 2}`] = taskEndTimeIDs[`${old_end}`];
				delete taskEndTimeIDs[`${old_end}`];
			}
			var index = taskEndTimes.indexOf(old_end);
			taskEndTimes[index] = parseInt(event.target.style.top) + parseInt(event.target.style.height) + 2;
			$.ajax({
				type: "POST",
				contentType: "application/json;charset=utf-8",
				url: '/update_task/',
				data: JSON.stringify({ 'id': event.target.id, 'height': `${parseInt(event.target.style.height) + 2}`, 'top': event.target.style.top }), // serializes the form's elements.
				success: function (data) {
					event.target.querySelector(".taskText").innerHTML = `${data.task} from ${setTime(parseInt(event.target.style.top))} to ${setTime(parseInt(event.target.style.top) + parseInt(event.target.style.height) + 2)}`;
					event.target.style.height = parseInt(event.target.style.height) + 2;
					taskModal.style.display = "none";
					editTaskModal.style.display = "none";
					noClick = false
				}
			});
		},
		grid: [50, 10]
	});
});

function hexToRgbA(hex) {
	var c;
	if (/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
		c = hex.substring(1).split('');
		if (c.length == 3) {
			c = [c[0], c[0], c[1], c[1], c[2], c[2]];
		}
		c = '0x' + c.join('');
		return 'rgba(' + [(c >> 16) & 255, (c >> 8) & 255, c & 255].join(',') + ',.7)';
	}
	throw new Error('Bad Hex');
}




function indOrGrp() {
	if (document.getElementById('editSingleEvent').checked) {
		document.getElementById('editFrequency').style.visibility = 'hidden';
		document.getElementById('editFrequencyLabel').style.visibility = 'hidden';
	}
	else {
		document.getElementById('editFrequency').style.visibility = 'visible';
		document.getElementById('editFrequencyLabel').style.visibility = 'visible';
	}

}

$(function () {
	$(".dtpick").datepicker(
		{
			Format: "dd-mm-yy",
			dateFormat: "dd-mm-yy"
		}
	);
});

function set_message_count(n) {
	$('#message_count').text(n);
	$('#message_count').css('visibility', n ? 'visible' : 'hidden');
}