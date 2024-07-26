function gotoTop() {
  window.scroll({
    top: 0,
    behavior: "smooth",
  });
}
function gotoBottom() {
  var element = document.documentElement;
  var bottom = element.scrollHeight - element.clientHeight;
  window.scroll(0, bottom);
}
