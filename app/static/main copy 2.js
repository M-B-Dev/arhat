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
			location.reload();
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
	$.getJSON('/check_without_push', {},
	function(tasks) {
	  	modal.style.display = "none";
		fetch(`/complete?id=${tasks.id}`).then(response => (
			location.reload()
		));

		}

  );
  

});

var svgCanvas = document.querySelector("svg");
var svgNS = "http://www.w3.org/2000/svg";
var rectangles = [];

function Rectangle(x, y, w, h, svgCanvas) {
  this.x = x;
  this.y = y;
  this.w = w;
  this.h = h;
  this.stroke = 0;
  this.el = document.createElementNS(svgNS, "rect");
  this.el.setAttribute("data-index", rectangles.length);
  this.el.setAttribute("class", "edit-rectangle");
  this.el.innerText = 'Dragged in';
  rectangles.push(this);

  this.draw();
  svgCanvas.appendChild(this.el);
}

Rectangle.prototype.draw = function() {
  this.el.setAttribute("x", this.x);
  this.el.setAttribute("y", this.y);
  this.el.setAttribute("width", "100%");
  this.el.setAttribute("height", this.h);
  this.el.setAttribute("stroke-width", this.stroke);
  this.el.innerText = 'Dragged in';
  
};

interact(".edit-rectangle")
  // change how interact gets the
  // dimensions of '.edit-rectangle' elements
  .rectChecker(function(element) {
    // find the Rectangle object that the element belongs to
	var rectangle = rectangles[element.getAttribute("data-index")];
	rectangle.innerText = 'Dragged in';
    // return a suitable object for interact.js
    return {
      left: rectangle.x,
      top: rectangle.y,
      right: rectangle.x + rectangle.w,
      bottom: rectangle.y + rectangle.h
    };
  })
  .draggable({
    max: Infinity,
    inertia: true,
    listeners: {
      move(event) {
        var rectangle = rectangles[event.target.getAttribute("data-index")];

        rectangle.x = event.rect.left;
        rectangle.y = event.rect.top;
        rectangle.draw();
      }
    },
    modifiers: [
      interact.modifiers.restrictRect({
        // restrict to a parent element that matches this CSS selector
        restriction: "svg",
        // only restrict before ending the drag
        endOnly: true
      })
    ]
  })
  .resizable({
    edges: { left: true, top: true, right: true, bottom: true },
    listeners: {
      move(event) {
        var rectangle = rectangles[event.target.getAttribute("data-index")];
		console.log(event.rect.height);
        rectangle.w = event.rect.width;
        rectangle.h = event.rect.height;
        rectangle.x = event.rect.left;
        rectangle.y = event.rect.top;
        rectangle.draw();
      }
    },
    modifiers: [
      interact.modifiers.restrictEdges({ outer: "svg", endOnly: true }),
      interact.modifiers.restrictSize({ min: { width: 20, height: 20 } })
    ]
  });

interact.maxInteractions(Infinity);


var taskArea = document.getElementById('taskArea');
// taskArea.onclick = function(event) {
// 	console.log("clicked");
// 	new Rectangle(0, event.clientY, 20, 80, svgCanvas)
//   }



// for (var i = 0; i < 1; i++) {
//   ;
// }

// Get the modal
var taskModal = document.getElementById("myTaskModal");

// Get the <span> element that closes the modal
var spanTask = document.getElementsByClassName("task-close")[0];


// When the user clicks on the button, open the modal
taskArea.onclick = function(event) {
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


$(document).ready(function() {
	$('#tasks').submit(function (e) {
		taskModal.style.display = "none";
		$.ajax({
			type: "POST",
			url: '/new_task/',
			data: $('#tasks').serialize(), // serializes the form's elements.
			success: function (data) {
				new Rectangle(0, data.minutes, 20, data.height, svgCanvas)
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
