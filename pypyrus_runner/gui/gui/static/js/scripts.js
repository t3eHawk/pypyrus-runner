function hideNavigation() {
  var nav = document.getElementById("nav");
  var main = document.getElementById("main");
  if (nav.style.display === "none") {
    nav.style.display = "block";
    main.style.width = "calc(100% - 250px)";
  } else {
    nav.style.display = "none";
    main.style.width = "100%";
  }
}

function highlightActiveNavigation() {
  var menu = document.getElementById("menu");
  var href = window.location.pathname;
  var sel = "a[href='" + href + "']";
  var elem = menu.querySelectorAll(sel)[0];
  elem.classList.add("active");
}

function resize() {
  // width = window.innerWidth;
  // height = window.innerHeight;
  // var nav = document.getElementById("nav");
  // var main = document.getElementById("main");
  // if (width < 1920) {
  //   if (nav.style.display === "block") {
  //     nav.style.display = "none";
  //     main.style.width = "100%";
  //   }
  // }
  // else if (width >= 1920) {
  //   if (nav.style.display === "none") {
  //     nav.style.display = "block";
  //     main.style.width = "calc(100% - 250px)";
  //   }
  // }
}

window.onload = function() {
  highlightActiveNavigation()
}
