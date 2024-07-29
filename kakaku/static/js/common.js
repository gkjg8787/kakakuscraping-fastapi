function gotoTop() {
  const elem = document.getElementsByTagName("html");
  elem[elem.length - 1].scrollIntoView(true);
}
function gotoBottom() {
  const elem = document.getElementsByTagName("html");
  elem[elem.length - 1].scrollIntoView(false);
}
