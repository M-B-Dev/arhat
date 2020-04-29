// main.js

'use strict';

// const applicationServerPublicKey = "BNbxGYNMhEIi9zrneh7mqV4oUanjLUK3m+mYZBc62frMKrEoMk88r3Lk596T0ck9xlT+aok0fO1KXBLV4+XqxYM=";


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
	// TODO: Send subscription to application server

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
		.then(function(subscription) {
			fetch(`/sub`);
			$.ajax({
				type: "POST",
				url: "/subscribe/",
				contentType: 'application/json; charset=utf-8',
				dataType:'json',
				data: JSON.stringify({'sub_token':subscription}),
				success: function( data ){
			},
			error: function( jqXhr, textStatus, errorThrown ){
			}
			});
			updateSubscriptionOnServer(subscription);
			localStorage.setItem('sub_token',JSON.stringify(subscription));
			isSubscribed = true;
			location.reload();
			updateBtn();
		})
		
		.catch(function(err) {
			updateBtn();
		});

}

function unsubscribeUser() {
	fetch(`/unsubscribe`);
	swRegistration.pushManager.getSubscription()
		.then(function(subscription) {
			if (subscription) {
				return subscription.unsubscribe();
			}
		})
		.catch(function(error) {
		})
		.then(function() {
			updateSubscriptionOnServer(null);

			isSubscribed = false;

			updateBtn();
		});
}

function initializeUI() {
	pushButton.addEventListener('click', function() {
		pushButton.disabled = true;
		if (isSubscribed) {
			unsubscribeUser();
		} else {
			subscribeUser();
		}
	});

	// Set the initial subscription value
	swRegistration.pushManager.getSubscription()
		.then(function(subscription) {
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
		.then(function(swReg) {
			swRegistration = swReg;
			initializeUI();
		})
		.catch(function(error) {
		});
} else {
	pushButton.textContent = 'Push Not Supported';
}

$(document).ready(function(){
	$.ajax({
		type:"GET",
		url:'/subscription/',
		success:function(response){
			localStorage.setItem('applicationServerPublicKey',response.public_key);
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

// var svgCanvas = document.querySelector("svg");
// var svgNS = "http://www.w3.org/2000/svg";
// var rectangles = [];

// function Rectangle(x, y, w, h, svgCanvas, task, id) {
//   this.x = x;
//   this.y = y;
//   this.w = w;
//   this.h = h;
//   this.stroke = 0;
//   this.id = id;
//   this.el = document.createElementNS(svgNS, "rect");
//   this.text = document.createElementNS(svgNS, "text");
//   this.text.textContent = task;
//   this.el.setAttribute("data-index", rectangles.length);
//   this.el.setAttribute("class", "edit-rectangle");
//   this.text.setAttribute("class", "edit-text");
//   rectangles.push(this);

//   this.draw();
//   svgCanvas.appendChild(this.el);
//   svgCanvas.appendChild(this.text);
// }

// Rectangle.prototype.draw = function() {
//   this.el.setAttribute("x", this.x);
//   this.el.setAttribute("y", this.y);
//   this.el.setAttribute("width", "100%");
//   this.el.setAttribute("height", this.h);
//   this.el.setAttribute("stroke-width", this.stroke);
//   this.text.setAttribute("x", '50%');
//   this.text.setAttribute("y", this.y + (this.h/2));
//   this.text.setAttribute('text-anchor', "middle");
//   this.text.setAttribute('alignment-baseline', "middle");
//   this.el.setAttribute('id', this.id);
  
// };

// interact(".edit-rectangle")
//   // change how interact gets the
//   // dimensions of '.edit-rectangle' elements
//   .rectChecker(function(element) {
//     // find the Rectangle object that the element belongs to
// 	var rectangle = rectangles[element.getAttribute("data-index")];
//     // return a suitable object for interact.js
//     return {
//     //   left: rectangle.x,
//       top: rectangle.y,
//     //   right: rectangle.x + rectangle.w,
//       bottom: rectangle.y + rectangle.h
//     };
//   })
//   .draggable({
//     max: Infinity,
//     inertia: true,
//     listeners: {

			
//       move(event) {
// 		var rectangle = rectangles[event.target.getAttribute("data-index")];
//         // rectangle.x = event.rect.left;
//         rectangle.y = event.rect.top;
//         rectangle.draw();
//       }
//     },
//     modifiers: [
//       interact.modifiers.restrictRect({
//         // // restrict to a parent element that matches this CSS selector
//         // restriction: "svg",
//         // // only restrict before ending the drag
//         // endOnly: true
//       })
//     ]
//   })
//   .resizable({
//     edges: { left: true, top: true, right: true, bottom: true },
//     listeners: {
//       move(event) {
// 		var rectangle = rectangles[event.target.getAttribute("data-index")];


		
// 		// console.log(`this is ${event.rect.bottom} ${event.rect.top}`);
// 		// console.log(`this is the id ${event.target.id}`)
//         // rectangle.w = event.rect.width;
//         rectangle.h = event.rect.height;
//         // rectangle.x = event.rect.left;
//         rectangle.y = event.rect.top;
//         rectangle.draw();
// 	  }
	  
//     },
//     modifiers: [

//       interact.modifiers.restrictEdges({ outer: "svg", endOnly: true }),
//       interact.modifiers.restrictSize({ min: { width: 20, height: 20 } })
// 	]
	
//   });

// interact.maxInteractions(Infinity);


var taskArea = document.getElementById('taskArea');
// taskArea.onclick = function(event) {
// 	console.log("clicked");
// 	new Rectangle(0, event.clientY, 20, 80, svgCanvas)
//   }

function setTime(pos, elID){
	var num = pos;
	var hours = (num / 60);
	var rhours = Math.floor(hours);
	var minutes = (hours - rhours) * 60;
	var rminutes = Math.round(minutes);
	if (rhours < 10 && rminutes < 10) {
		document.getElementById(elID).value = `0${rhours.toString()}:0${rminutes.toString()}`;
	}
	else if (rhours > 9 && rminutes < 10) {
		document.getElementById(elID).value = `${rhours.toString()}:0${rminutes.toString()}`;
	}
	else if (rhours < 10 && rminutes > 9) {
		document.getElementById(elID).value = `0${rhours.toString()}:${rminutes.toString()}`;
	}
	else {
		document.getElementById(elID).value = `${rhours.toString()}:${rminutes.toString()}`;
	}
};

function Returntime(pos){
	var num = pos;
	var hours = (num / 60);
	var rhours = Math.floor(hours);
	var minutes = (hours - rhours) * 60;
	var rminutes = Math.round(minutes);
	if (rhours < 10 && rminutes < 10) {
		return `0${rhours.toString()}:0${rminutes.toString()}`
	}
	else if (rhours > 9 && rminutes < 10) {
		return `${rhours.toString()}:0${rminutes.toString()}`
	}
	else if (rhours < 10 && rminutes > 9) {
		return `0${rhours.toString()}:${rminutes.toString()}`
	}
	else {
		return `${rhours.toString()}:${rminutes.toString()}`;
	}
};

if (document.getElementById("timeline")){
var timeline = document.getElementById("timeline");
timeline.style.left = '0px';
var nextDate = new Date();
nextDate.setHours(24);
nextDate.setMinutes(0);
var now = 1440-(((nextDate-new Date())/60)/1000);
timeline.style.top = now;

setInterval(timeLine, 60000);
var pushed_task = false;

function timeLine() {
var nextDate = new Date();
nextDate.setHours(24);
nextDate.setMinutes(0);
var now = 1440-(((nextDate-new Date())/60)/1000);
timeline.style.top = now;
console.log(`${now}`);
if (taskEndTimes.includes(now)){
	console.log(toString(now));
	console.log(taskEndTimes);
	console.log(taskEndTimeIDs);
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
      button.onclick = function() {
          modal.style.display = "none";
          fetch(`/complete?id=${taskEndTimeIDs[unlock][0]}`).then(response => (
              location.reload()
          ));
          
      }
    
      button2.onclick = function() {
        modal.style.display = "none";

    } 
}
};
};

var taskEndTimeIDs = {};
var taskEndTimes = [];

function Rectangle(ypos, height, task, id, color, frequency)
	{
		var newTask = document.createElement("DIV");
		newTask.innerHTML = `<div class='taskText'>${task} from ${Returntime(ypos)} to ${Returntime(ypos+height)}</div>`;
		newTask.setAttribute('id', id);
		newTask.setAttribute('class', "ui-widget-content draggable");
		newTask.style.left = '0px';
		newTask.style.top = `${ypos}px`;
		newTask.style.height = `${height}px`;
		newTask.style.width = `${taskArea.clientWidth}px`; 
		newTask.style.backgroundColor = hexToRgbA(`#${color}`)
		taskArea.appendChild(newTask);
		taskEndTimeIDs[`${ypos+height}`] = [id, task];
		taskEndTimes.push(ypos+height);
		newTask.onclick = function(e){
			document.addEventListener("click",handler,true);
			console.log(e.target.style.top);
			editTaskModal.style.display = "block";
			var top = parseInt(e.target.style.top);
			setTime(top, "editStart");
			setTime(top+parseInt(e.target.style.height), "end");
			e.stopPropagation();
			document.getElementById("taskEdit").value = task
			document.getElementById("editColor").value = color;
			document.getElementById('editID').value = id;
			if (frequency == "None"){
				document.getElementById('editFrequency').value = '';
				document.getElementById('editSingleEvent').style.visibility = 'hidden';
			}
			else{
			document.getElementById('editFrequency').value = frequency;
			};
			console.log($('#editDate'))			
		}
		
			
		
	};
	
var leftCol = document.getElementById("colLeft");
var toAdd = document.createDocumentFragment();
for (var i = 0; i < 1440; i++) {
	if (i == 0) {
		console.log(i)
		var newHour = document.createElement("P");
		newHour.innerHTML = i + ":00";
		newHour.setAttribute('class', "timeHour");
		newHour.style.position = "absolute";
		newHour.setAttribute('id', `a${i}`);
		newHour.style.left = '50%';
		newHour.style.top = `${i}px`;
		toAdd.appendChild(newHour);
	}
	else if (i % 60 == 0){
		console.log(i)
		var newHour = document.createElement("P");
		newHour.style.position = "absolute";
		newHour.innerHTML = (i/60)+ ":00";
		newHour.setAttribute('id', `a${i}`);
		newHour.setAttribute('class', "timeHour");
		newHour.style.left = '50%';
		newHour.style.top = `${i}px`;
		toAdd.appendChild(newHour);
	}
}
leftCol.appendChild(toAdd);

// Get the modal
var taskModal = document.getElementById("myTaskModal");
var editTaskModal = document.getElementById("myEditTaskModal");
// Get the <span> element that closes the modal
var spanTask = document.getElementsByClassName("task-close")[0];
var spanEditTask = document.getElementsByClassName("task-close")[1];

// When the user clicks on the button, open the modal
taskArea.onclick = function(event) {
	document.addEventListener("click",handler,true);
	taskModal.style.display = "block";
	console.log(event.offsetY)
	if (event.offsetY < 60) {
		document.getElementById("start").value = `00:00`;
	}
	else if (event.offsetY < 600){
		console.log('under 600');
		document.getElementById("start").value = `0${String(event.offsetY/60).charAt(0)}:00`;
	}
	else {
		console.log(String(event.offsetY/60).substring(0,2));
		document.getElementById("start").value = `${String(event.offsetY/60).substring(0,2)}:00`;
	}
	
  	}

// When the user clicks on <span> (x), close the modal
spanTask.onclick = function() {
	taskModal.style.display = "none";
}

spanEditTask.onclick = function() {
	editTaskModal.style.display = "none";
}



$(document).ready(function() {
	$('#tasks').submit(function (e) {
		console.log('running')
		taskModal.style.display = "none";
		$.ajax({
			type: "POST",
			url: '/new_task/',
			data: $('#tasks').serialize(), // serializes the form's elements.
			success: function (data) {
				new Rectangle(data.minutes, data.height, data.task, data.id, data.color, data.frequency);
				location.reload()
				// new Rectangle(0, data.minutes, 20, data.height, svgCanvas, data.task, data.id)
			}
		});
		e.preventDefault(); // block the traditional submission of the form.
	}); 
	// Inject our CSRF token into our AJAX request.
	$.ajaxSetup({
		beforeSend: function(xhr, settings) {
			if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
				xhr.setRequestHeader("X-CSRFToken", "{{ form.csrf_token._value() }}")
			}
		}
	})
});

var noClick = false;
document.addEventListener("click",handler,true);
function handler(e){
	if(noClick==true){
	e.stopPropagation();
	e.preventDefault();
	}
	else{
		document.removeEventListener('click', handler)
	}
}


$( function() {


    $( ".draggable" ).draggable(
      {
		start: function(event, ui){
			noClick = true;
		},
        axis: "y",
        containment: "parent",
		grid: [ 50, 10 ],
		stop: function(event, ui) {
			console.log(taskEndTimeIDs)
			console.log(taskEndTimes)
			var old_end = ui.originalPosition.top+parseInt(event.target.style.height);
			console.log(`${parseInt(event.target.style.top)+parseInt(event.target.style.height)}`)
			console.log(old_end);
			if (parseInt(event.target.style.top)+parseInt(event.target.style.height) != old_end) 
			{
				taskEndTimeIDs[`${parseInt(event.target.style.top)+parseInt(event.target.style.height)}`] = taskEndTimeIDs[`${old_end}`];
				delete taskEndTimeIDs[`${old_end}`];
			}
			var index = taskEndTimes.indexOf(old_end);
			taskEndTimes[index] = parseInt(event.target.style.top)+parseInt(event.target.style.height)
			console.log(taskEndTimeIDs)
			console.log(taskEndTimes)
			$.ajax({
			type: "POST",
			contentType: "application/json;charset=utf-8",
			url: '/update_task/',
			data: JSON.stringify({'id' : event.target.id, 'height' :  event.target.style.height, 'top' : event.target.style.top }), // serializes the form's elements.
			success: function (data) {
				event.target.querySelector(".taskText").innerHTML = `${data.task} from ${Returntime(parseInt(event.target.style.top))} to ${Returntime(parseInt(event.target.style.top)+parseInt(event.target.style.height))}`;

				taskModal.style.display = "none";
				editTaskModal.style.display = "none";
				noClick = false;
				
			}
		});
	}
      }
    ).resizable({
		start: function(event, ui){
			noClick = true;
		},
		// ghost: true,
		// animate: true,
      containment: "parent",
     
	  handles: 'n, s',
	  stop: function(event, ui) {
		// var resized = $(this);
		// console.log(resized)
		// resized.queue(function() {
		// 	resizeComplete(resized);
		// 	$( this ).dequeue();
		//   });
		// console.log(ui)
		console.log(taskEndTimeIDs)
		console.log(taskEndTimes)
		var old_end = ui.originalPosition.top+ui.originalSize.height+2;
		console.log(old_end)
		if (parseInt(event.target.style.top)+parseInt(event.target.style.height) != old_end) {
		taskEndTimeIDs[`${parseInt(event.target.style.top)+parseInt(event.target.style.height)+2}`] = taskEndTimeIDs[`${old_end}`];
		delete taskEndTimeIDs[`${old_end}`];
		}
		var index = taskEndTimes.indexOf(old_end);
		taskEndTimes[index] = parseInt(event.target.style.top)+parseInt(event.target.style.height)+2;
		console.log(taskEndTimeIDs);
		console.log(taskEndTimes);
		$.ajax({
		type: "POST",
		contentType: "application/json;charset=utf-8",
		url: '/update_task/',
		data: JSON.stringify({'id' : event.target.id, 'height' :  `${parseInt(event.target.style.height)+2}`, 'top' : event.target.style.top }), // serializes the form's elements.
		success: function (data) {
			event.target.querySelector(".taskText").innerHTML = `${data.task} from ${Returntime(parseInt(event.target.style.top))} to ${Returntime(parseInt(event.target.style.top)+parseInt(event.target.style.height)+2)}`;
			event.target.style.height = parseInt(event.target.style.height)+2;
			console.log(event.target.style.height);
			taskModal.style.display = "none";
			editTaskModal.style.display = "none";
			noClick = false
		}
	});
},
grid: [ 50, 10 ]
		// stop: function(event, ui) {
		// 	var resized = $(this);
		// 	resized.queue(function() {
		// 	 (function() {
		// 		 console.log(ui.element.attributes);
		// 		ui.element.attributes.style.width = '100%';
		// 		 alert("resized")
		// 	 })()
		// 	  $( this ).dequeue();
		// 	});
		// },

	});
  });

  $(document).ready(function() {
	$('#editTasks').submit(function (e) {
		editTaskModal.style.display = "none";
		$.ajax({
			type: "POST",
			url: '/edit_task/',
			data: $('#editTasks').serialize(), // serializes the form's elements.
			success: function (data) {
				window.location.href = `index/ph?r=#${data.id}`
				
				window.location.reload(true)
				console.log(`index/ph?r=#${data.id}`)
				// new Rectangle(0, data.minutes, 20, data.height, svgCanvas, data.task, data.id)
			}
		});
		e.preventDefault(); // block the traditional submission of the form.
	}); 
	// Inject our CSRF token into our AJAX request.
	$.ajaxSetup({
		beforeSend: function(xhr, settings) {
			if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
				xhr.setRequestHeader("X-CSRFToken", "{{ form.csrf_token._value() }}")
			}
		}
	})
});

function hexToRgbA(hex){
    var c;
    if(/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)){
        c= hex.substring(1).split('');
        if(c.length== 3){
            c= [c[0], c[0], c[1], c[1], c[2], c[2]];
        }
        c= '0x'+c.join('');
        return 'rgba('+[(c>>16)&255, (c>>8)&255, c&255].join(',')+',.7)';
    }
    throw new Error('Bad Hex');
}

// function resizeComplete(element) {
// 	element.context.style.width = '100%';
//  }




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
