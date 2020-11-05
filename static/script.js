$("#messages").on("click", ".followed", removeFollow);
$("#messages").on("click", ".not-followed", addFollow);

async function removeFollow(evt) {
  console.log("remove");
  msgId = $(this).data("id");
  res = await axios.post(`/users/remove_like/${msgId}`);
  $(this).removeClass("followed btn-primary");
  $(this).addClass("not-followed btn-secondary");
}

async function addFollow(evt) {
  console.log("add");
  msgId = $(this).data("id");
  res = await axios.post(`/users/add_like/${msgId}`);
  $(this).removeClass("not-followed btn-secondary");
  $(this).addClass("followed btn-primary");
}

$("#liked-messages").on("click", ".followed", deleteFollow);

async function deleteFollow(evt) {
  console.log("remove");
  msgId = $(this).data("id");
  res = await axios.post(`/users/remove_like/${msgId}`);
  $(this).remove();
}
