$("#messages").on("click", ".followed", removeFollow);
$("#messages").on("click", ".not-followed", addFollow);

function removeFollow(evt) {
  console.log(evt.target);
}

function addFollow(evt) {
  console.log(evt.target);
}
