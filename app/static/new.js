var svgCanvas = document.querySelector("svg");
var svgNS = "http://www.w3.org/2000/svg";
var rectangles = [];

function Rectangle(x, y, w, h, svgCanvas) {
  this.x = x;
  this.y = y;
  this.w = w;
  this.h = h;
  this.stroke = 5;
  this.el = document.createElementNS(svgNS, "rect");

  this.el.setAttribute("data-index", rectangles.length);
  this.el.setAttribute("class", "edit-rectangle");
  rectangles.push(this);

  this.draw();
  svgCanvas.appendChild(this.el);
}

Rectangle.prototype.draw = function() {
  this.el.setAttribute("x", this.x + this.stroke / 2);
  this.el.setAttribute("y", this.y + this.stroke / 2);
  this.el.setAttribute("width", this.w);
  this.el.setAttribute("height", this.h - this.stroke);
  this.el.setAttribute("stroke-width", this.stroke);
};

interact(".edit-rectangle")
  // change how interact gets the
  // dimensions of '.edit-rectangle' elements
  .rectChecker(function(element) {
    // find the Rectangle object that the element belongs to
    var rectangle = rectangles[element.getAttribute("data-index")];

    // return a suitable object for interact.js
    return {
    //   left: rectangle.x,
      top: rectangle.y,
    //   right: rectangle.w,
      bottom: rectangle.y + rectangle.h
    };
  })
  .draggable({
    max: Infinity,
    inertia: true,
    listeners: {
      move(event) {
        var rectangle = rectangles[event.target.getAttribute("data-index")];

        // rectangle.x = event.rect.left;
        rectangle.y = event.rect.top;
        rectangle.draw();
      }
    },
    modifiers: [
      interact.modifiers.restrictRect({
        // restrict to a parent element that matches this CSS selector
        // restriction: "svg",
        // only restrict before ending the drag
        // endOnly: false
// restrict to a parent element that matches this CSS selector
drag: 'svg',
// only restrict before ending the drag
endOnly: true,
// // consider the element's dimensions when restricting
// elementRect: { top: 0, left: 0, bottom: 1, right: 1 }
      })
    ]
  })
  .resizable({
    edges: { left: true, top: true, right: true, bottom: true },
    listeners: {
      move(event) {
        var rectangle = rectangles[event.target.getAttribute("data-index")];

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

for (var i = 0; i < 1; i++) {
  new Rectangle(0, 20, '%100', 80, svgCanvas);
}