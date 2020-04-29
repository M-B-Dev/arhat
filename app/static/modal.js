// Get the modal
var modal = document.getElementById("myModal");

// Get the button that opens the modal
var btn = document.getElementById("myBtn");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];


// When the user clicks on the button, open the modal

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
  else if (event.target == taskModal) {
	  
    taskModal.style.display = "none";
  }
}
var done = false;



// function sendNotifications() {
//   $.getJSON('/check', {},
//   function(todos) {
//       console.log(todos)
//     if (todos.todo != "nothing") {

//       modal.style.display = "block";
//     //   $('#modal-title').html(
//     //     `${todos.todo}`
//     // );
//     //   $('#button').html(
//     //       `<button class="btn btn-outline-success flashing effect" style="display: inline-block"> I have done this</button>`
//     //   );
//     //   $('#button2').html(
//     //     `<button class="btn btn-outline-danger flashing effect" style="display: inline-block"> I have not done this</button>`
//     // );
//     //   var button = document.getElementsByClassName("flashing effect")[0];
//     //   button.onclick = function() {
//     //       modal.style.display = "none";
//     //       fetch(`/complete?id=${todos.id}`).then(response => (
//     //           location.reload()
//     //       ));
          
//     //   }
    
//     //   button2.onclick = function() {
//     //     modal.style.display = "none";

//     // } 

//     }
    
//   }
// );
// }

// function callEveryHour() {
//   sendNotifications();
//   setInterval(sendNotifications, 1000*60*60);
// }



// var nextDate = new Date();
// if (nextDate.getMinutes() === 0) { // You can check for seconds here too
//     callEveryHour()
// } else {
//   var nextDate = new Date();
//     nextDate.setHours(24);
//     nextDate.setMinutes(0);
//     var now = 1440-(((nextDate-new Date())/60)/1000)

//     console.log(now)
//     console.log(nextDate)
//     console.log(Date())
//     var difference = nextDate - new Date();
//     console.log(difference)
//     setTimeout(callEveryHour, difference);
// }

