$(document).ready(function(){
	
	var owl = $('.owl-carousel');
	owl.owlCarousel({
		loop: true,
		nav: true,
		margin: 10,
		navigation : true,
		navigationText : ['<span class="fa-stack"><i class="fa fa-circle fa-stack-1x"></i><i class="fa fa-chevron-circle-left fa-stack-1x fa-inverse"></i></span>','<span class="fa-stack"><i class="fa fa-circle fa-stack-1x"></i><i class="fa fa-chevron-circle-right fa-stack-1x fa-inverse"></i></span>'],
		slideBy: 1,
		responsive: {
			0: {
				items: 1
			},
			600: {
				items: 3
			},
			960: {
				items: 5
			},
			1200: {
				items: 6
			}
		}
	});
	
	owl.on('mousewheel', '.owl-stage', function(e) {
		if (e.deltaY > 0) {
			owl.trigger('next.owl');
		} else {
			owl.trigger('prev.owl');
		}
		e.preventDefault();
	});

	$(".module-link").on("click",function(e) {
		var id = "#" + $(this).attr('id');
		e.preventDefault();
		$.get('https://finbyz.tech/modules', null, function(text){
			html = $(text).find(id).html();
			frappe.msgprint(__(html.toString()), __("Module"));
		});
	});
	
	$(".hover-link").on("click",function(e) {
		var id = "#" + $(this).attr('id') + "_msg";
		e.preventDefault();
		html = $(id).html();
		frappe.msgprint(__(html.toString()), __("IT Consulting"));
		
	});
});

$(".modules-sub").hover(
	function() {
		TweenLite.to($(this).find(".modules-div"), 1, {css:{height:"100%",opacity:"0.9"}, ease:Sine.easeOut});
		TweenLite.to($(this).find(".modules-sub-text"), 1.1, {css:{display:"initial"}, ease:Sine.easeOut});
	}, 
	function() {
		TweenLite.to($(this).find(".modules-div"), 1, {css:{height:"40%",opacity:"1"}, ease:Sine.easeOut});
		TweenLite.to($(this).find(".modules-sub-text"), 0.3, {css:{display:"none"}, ease:Sine.easeOut});
	}
);

$(".hover-sub").hover(
	function() {
		TweenLite.to($(this).find(".hover-div"), 1, {css:{height:"100%",opacity:"0.9"}, ease:Sine.easeOut});
		TweenLite.to($(this).find(".hover-sub-text"), 1.1, {css:{display:"initial"}, ease:Sine.easeOut});
	}, 
	function() {
		TweenLite.to($(this).find(".hover-div"), 1, {css:{height:"30%",opacity:"1"}, ease:Sine.easeOut});
		TweenLite.to($(this).find(".hover-sub-text"), 0.3, {css:{display:"none"}, ease:Sine.easeOut});
	}
);

/*  flipbox */
//IE doesn't transform-style:preserve-3d.
// for IE try https://codepen.io/rhernando/pen/vjGxH


//using TweenLite.set() takes care of all vendor-prefixes
TweenLite.set(".cardWrapper", {perspective:800});
TweenLite.set(".card", {transformStyle:"preserve-3d"});
TweenLite.set(".back", {rotationY:-180});
TweenLite.set([".back", ".front"], {backfaceVisibility:"hidden"});

$(".cardWrapper").hover(
  function() {
    TweenLite.to($(this).find(".card"), 1.2, {rotationY:180, ease:Back.easeOut});
  },
  function() {
    TweenLite.to($(this).find(".card"), 1.2, {rotationY:0, ease:Back.easeOut});  
  }
);

//a nice little intro;)
TweenMax.staggerTo($(".card"), 0.5, {rotationY:-180, repeat:1, yoyo:true}, 0.1);

$(function() {
  // init controller
	var controller = new ScrollMagic.Controller({globalSceneOptions: {triggerHook:"onEnter",duration: "135%"}});
	

	
	
	/* var timeline_scene = new TimelineMax();
	timeline_scene
		.to(".timeline .content", 2,{x:20;opacity:"1"})
		.to(".timeline-icon", 2,{x:20;opacity:"1"})
		; */
	
	// build scenes
	new ScrollMagic.Scene({triggerElement: "#parallax"})
					.setTween("#parallax > div", {y: "80%", ease: Linear.easeNone})
					.addTo(controller);

	
	/* new ScrollMagic.Scene({triggerElement: ".timeline"})
					.setTween(timeline_scene)
					.addTo(controller); */	


	var scrollController = new ScrollMagic.Controller();
	
	var parallax_all = new TimelineMax();
	parallax_all	
		.from("#Boat", 4 , {x:-700, ease: Power1.easeIn})	
		.from("#steer_text",1,{y:500,opacity:0},2)
		.from("#steer_sub_text",1,{y:550,opacity:0},3);
		
	new ScrollMagic.Scene({
			triggerElement: "#parallax",
			triggerHook:0.8,
			reverse:true
		})
		.setTween(parallax_all)
		.addTo(scrollController);
		

	$(".finbyz-fadeinup").each(function(){
		var fadeUpScene = new ScrollMagic.Scene({
			triggerElement: this,
			triggerHook: 0.8
		})
		.setTween(TweenMax.from(this, 0.8, {y: 50, opacity: 0, ease: Power1.easeIn}))
		.addTo(scrollController)
	})
	
	$(".finbyz-fadeinup-footer").each(function(){
		var fadeUpScene = new ScrollMagic.Scene({
			triggerElement: this,
			triggerHook: 1
		})
		.setTween(TweenMax.from(this, 0.8, {y: 50, opacity: 0, ease: Power1.easeIn}))
		.addTo(scrollController)
	})
	
	$(".finbyz-fadeindown").each(function(){
		var fadeUpScene = new ScrollMagic.Scene({
			triggerElement: this,
			triggerHook: 0.8
		})
		.setTween(TweenMax.from(this, 0.8, {y: -50, opacity: 0, ease: Power1.easeIn}))
		.addTo(scrollController)
	})

	$(".finbyz-zoomin").each(function(){
		var fadeUpScene = new ScrollMagic.Scene({
			triggerElement: this,
			triggerHook: 0.8
		})
		.setTween(TweenMax.from(this, 0.8, {scale: 0, ease: Power1.easeIn}))
		.addTo(scrollController)
	})

	$(".card").each(function(){
		var tl_card = new TimelineMax();
		tl_card.to(this, 1.2, {rotationY:180, ease:Back.easeOut})
				.to(this, 1.2, {rotationY:0, ease:Back.easeOut, delay: 0.5});

		var fadeUpScene = new ScrollMagic.Scene({
			triggerElement: this,
			triggerHook: 0.8,
			reverse: false
		})
		.setTween(tl_card)
		.addTo(scrollController)
	})
	/* $(window).scroll(function() {
		var navscene =  new ScrollMagic.Scene({
				triggerElement: ".main-content",
			})
			.addTo(scrollController)
			
			.on('enter',function(event){
				console.log(event.scrollDirection);
				if(event.scrollDirection == "FORWARD"){
						$('.navbar-default').removeClass('animated swingInX');
						$('.navbar-default').addClass('animated swingOutX');
					}
				if(event.scrollDirection == "REVERSE"){
						$('.navbar-default').removeClass('animated swingOutX');
						$('.navbar-default').addClass('animated swingInX');
					}
				});
	}); */
	var lastScrollTop = 0;
		// element should be replaced with the actual target element on which you have applied scroll, use window in case of no target element.
		window.addEventListener("scroll", function(){ // or window.addEventListener("scroll"....
		   var st = window.pageYOffset || document.documentElement.scrollTop; // Credits: "https://github.com/qeremy/so/blob/master/so.dom.js#L426"
		   if (st > lastScrollTop){
			  $('.navbar-default').removeClass('animated swingInX');
			  $('.navbar-default').addClass('animated swingOutX');
		   } else {
			  $('.navbar-default').removeClass('animated swingOutX');
			  $('.navbar-default').addClass('animated swingInX');
		   }
		   lastScrollTop = st <= 0 ? 0 : st; // For Mobile or negative scrolling
		}, false);
	
	

});
