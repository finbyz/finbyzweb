frappe.ready(function() {
	var seen = [];
	var last = 0;

	setInterval(function() {
		var whats = [
			'Passion', 'Expertise', 'Creativity', 'Innovation', 'Understanding',
		];

		if(seen.length == whats.length) {
			seen = []
		}

		var index = parseInt(Math.random() * whats.length);
		while(seen.includes(index) || last == index) {
			index = parseInt(Math.random() * whats.length);
		}

		var what = whats[index];

		seen.push(index);
		last = index;

		var start = 0;
		for(var i = 0; i < what.length; i++) {
			var text = what.substr(0, i + 1);
			start += 50 + Math.random() * 50;
			show_text(text, start);
		}
	}, 3000)

	function show_text(text, timeout) {
		setTimeout(() => {
			$('.what').text(text);
		}, timeout)
	}

});


	
$(document).ready(function(){
   
   	// Fakes the loading setting a timeout
     setTimeout(function() {
         $('body').addClass('loaded');
     }, 500);

	$(".carousel").carousel();
	
	var owl = $('.owl-carousel');
	owl.owlCarousel({		
		loop: true,
		nav: true,
		margin: 10,
		navigation: true,
		navigationText: ['<span class="fa-stack"><i class="fa fa-circle fa-stack-1x"></i><i class="fa fa-chevron-circle-left fa-stack-1x fa-inverse"></i></span>', '<span class="fa-stack"><i class="fa fa-circle fa-stack-1x"></i><i class="fa fa-chevron-circle-right fa-stack-1x fa-inverse"></i></span>'],
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
		$.get('/modules', null, function(text){
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
		$('.hover-sub-text p').addClass('t-white p-10');
		TweenLite.to($(this).find(".hover-sub-text"), 1.1, {css:{display:"initial"}, ease:Sine.easeOut});
	}, 
	function() {
		TweenLite.to($(this).find(".hover-div"), 1, {css:{height:"20%",opacity:"1"}, ease:Sine.easeOut});
		
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
// set some global properties
	TweenLite.set('.client-grid-wrap', {perspective:1000});
	TweenLite.set('.client-grid-wrap-inner', {transformStyle:"preserve-3d"});
	TweenLite.set('.grid-back', {rotationX:-90});
	TweenLite.set(['.grid-back', '.grid-front'], {backfaceVisibility:"hidden", transformOrigin:'50% 0'});

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
  	
	/* new ScrollMagic.Scene({triggerElement: ".timeline"})
					.setTween(timeline_scene)
					.addTo(controller); */	


	var scrollController = new ScrollMagic.Controller();
	
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

	
// set some global properties
TweenLite.set('.client-grid-wrap', {perspective:1000});
TweenLite.set('.client-grid-wrap-inner', {transformStyle:"preserve-3d"});
TweenLite.set('.grid-back', {rotationX:-90});
TweenLite.set(['.grid-back', '.grid-front'], {backfaceVisibility:"hidden", transformOrigin:'50% 0'});

// loop through each element
	$(".client-grid-wrapper").each(function(i, el) {
		
	  // create a timeline for this element in paused state
	  var tl = new TimelineMax({paused: true});

	  // create your tween of the timeline in a variable
	  var t = tl
			 .set(el,{willChange:"transform"})
			 .to($(el).find('.client-grid-wrap-inner'), 0.53, {y:"-40px", rotationX:90, zIndex: 2, overwrite:"all", ease:Back.easeOut}, 0);

	  // store the tween timeline in the javascript DOM node
	  el.animation = t;

	  //create the event handler
	  $(el).on("mouseenter",function(){
		this.animation.play();
	  }).on("mouseleave",function(){
		this.animation.reverse();
	  });
	  
	});
		
});
