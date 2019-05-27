$(document).ready(function () {
	/* video js */
	var video = document.getElementById("myVideo");
        video.addEventListener("canplay", function() {
            video.play();
        });
        video.addEventListener("ended", function() {
        setTimeout(function() {
            video.play();
        }, 6000);
        });
 });