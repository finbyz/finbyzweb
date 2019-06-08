var loc = window.location.pathname;

$(".nav .nav-item a.nav-active").each(function(){
  $(this).parent( 'li' ).toggleClass('active', $(this).attr('href') == loc);
});

$(".tabanchor").click(
	function () {
		TweenMax.from('.flex-inner', 0.8, { scale: 0, ease: Power1.easeIn })
	}
)
$(".ind-module .nav-pills .nav-link").click(
	function () {
		TweenMax.from('.tab-pane', 0.8, { y: 150, opacity: 0, ease: Power1.easeIn })
	}
) 

$(document).ready(function () {
	
	/* phase js */
	$('.tabanchor').on('click', function (e) {
        var getTab = $(this).attr('href');
        $('.circle-icon').removeClass('active');
        $(this).parent().addClass('active');
        $('.flex-inner').removeClass('active')
        $(getTab).addClass('active')
        e.preventDefault();

    })
	
	var $tab = window.location.hash.replace('#', '');
	showProjects($tab, 20);

	$(".parent-category").click(function () {
		var selectedClass = $(this).attr("data-rel");
		if (selectedClass == "all") {
			$(".gallery-sub-category-button").removeClass("d-visible");
			$(".gallery-sub-category-button").addClass("d-none");
		}
		$(".gallery-sub-category-button").removeClass("d-visible");
		$(".gallery-sub-category-button." + selectedClass).addClass("d-visible");
	});
	$('.filter').on('click', function () {
		var cat = $(this).attr("data-rel");
		if (cat == 'all') {
			$('.gallery-filter').removeClass('d-none');
			setTimeout(function () {
				$('.gallery-filter').removeClass('d-none');
			}, 300);
		} else {
			$('.gallery-filter').addClass('d-none');
			setTimeout(function () {
				$('.gallery-filter.' + cat).removeClass('d-none');
			}, 300);
		}
	});
	var owl = $('.owl-carousel.module-carousel');
	owl.owlCarousel({
		autoplay: true,
		autoplayHoverPause: true,
		smartSpeed: 1200,
		loop: true,
		nav: true,
		dots:false,
		margin: 10,
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
				items: 5
			}
		}
	});

	owl.on('mousewheel', '.owl-stage', function (e) {
		if (e.deltaY > 0) {
			owl.trigger('next.owl');
		} else {
			owl.trigger('prev.owl');
		}
		e.preventDefault();
	});

	$(".module-link").on("click", function (e) {
		var id = "#" + $(this).attr('id');
		e.preventDefault();
		$.get('/modules-of-erp', null, function (text) {
			html = $(text).find(id).html();
			frappe.msgprint(__(html.toString()), __("Module"));
		});
	});

	$(".hover-link").on("click", function (e) {
		var id = "#" + $(this).attr('id') + "_msg";
		e.preventDefault();
		html = $(id).html();
		frappe.msgprint(__(html.toString()), __("IT Consulting"));

	});

	// inquiry form 
	// lead creation
		function lead_creation() {
			frappe.call({
					method: "finbyzweb.api.set_form_data",
					args:{
							'lead_name': $('#lead_name').val(),
							'company_name': $('#company_name').val(),
							'mobile_no': $('#mobile_no').val(),
							'title': document.title + '</br>' + window.location.href,
							'email': $('#email').val()
					},
					callback: function (r) {
							$('#lead_name').val('');
							$('#company_name').val('');
							$('#mobile_no').val('');
							$('#email').val('');
					}
			});
		};
		
		//validation and animation
		
 	$(function () {
		let show = 'show';
		
		$('.inquiry-main .inquiry-input').on('checkval', function () {
			let label = $(this).next('label');
			if(this.value !== '') {
				label.addClass(show);
			} else {
				label.removeClass(show);
			}
		}).on('keyup', function () {
			$(this).trigger('checkval');
		}); 
	 
	 });

		var form = $('#inquiry'),
		submit = form.find('[name="submit"]');

	form.on('submit', function(e) {
		e.preventDefault();
		
		// avoid spamming buttons
		if (submit.attr('value') !== 'Send')
			return;
		
		var valid = true;
		form.find('input').removeClass('invalid').each(function() {
			if (!this.value) {
				$(this).addClass('invalid');
				valid = false;
			}
		});
		
		if (!valid) {
			form.animate({left: '-3em'},  50)
					.animate({left:  '3em'}, 100)
					.animate({left:    '0'},  50);
			}
		else {
			submit.attr('value', 'Sending...');
			// simulate AJAX response
			setTimeout(function() {
				// step 1: slide labels and inputs
				// when AJAX responds with success
				// no animation for AJAX failure yet
				$( "#inquiry-form" ).toggle({ effect: "scale", direction: "vertical" });
				form.find('label')
				
						.animate({left: '100%'}, 500)
						.animate({opacity: '0'}, 500);
			}, 1000);
			setTimeout(function() {
				// step 2: show thank you message after step 1
				submit.attr('value', 'Thank you :)')
							.css({boxShadow: 'none'});
			}, 1000);
			setTimeout(function() {
				// step 3: reset
				$( "#inquiry-form" ).toggle({ effect: "scale", direction: "vertical" });
				
				form.find('label')
						.css({left: '0'})
						.animate({opacity: '1'}, 500);
				submit.attr('value', 'Send')
							.css({backgroundColor: ''});
							lead_creation();
			}, 3000);
			let show = 'show';
			$('.inquiry-main', function () {
					let label = $('.inquiry-label');
						label.removeClass(show);
					
				}); 
			}
	});

	var owl = $('.owl-carousel.main-carousel');
	  owl.owlCarousel({
		autoplay: true,
		autoplayHoverPause: true,
		smartSpeed: 800,
		loop: true,
		nav: false,
		navText: false,
		dots: false,
		mouseDrag: true,
		margin: 10,
		navigation: true,
		navigationText: ['<span class="fa-stack"><i class="fa fa-circle fa-stack-1x"></i><i class="fa fa-chevron-circle-left fa-stack-1x fa-inverse"></i></span>', '<span class="fa-stack"><i class="fa fa-circle fa-stack-1x"></i><i class="fa fa-chevron-circle-right fa-stack-1x fa-inverse"></i></span>'],
		slideBy: 1,
		items: 1,
		});
	
	 owl.on('changed.owl.carousel', function(e) {
		var scrollController = new ScrollMagic.Controller();
		
		$(".main-carousel #first-p").each(function () {
			var fadeUpScene = new ScrollMagic.Scene({
				triggerElement: this,
				triggerHook: 1
			})
				.setTween(TweenMax.from(this, 1, { scale: 0, ease: Power1.easeIn,delay:1 }))
			.addTo(scrollController)
		})
		$(".main-carousel .slide1 img").each(function () {
			var fadeUpScene = new ScrollMagic.Scene({
				triggerElement: this,
				triggerHook: 1
			})
				.setTween(TweenMax.from(this, 1, {x: 50, opacity: 0, ease: Power1.easeOut,delay:0.5}))
			.addTo(scrollController)
		})
		
	 });
	 

});

$(".modules-sub").hover(
	function () {
		TweenLite.to($(this).find(".modules-div"), 1, { css: { height: "100%", opacity: "0.9" }, ease: Sine.easeOut });
		TweenLite.to($(this).find(".modules-sub-text"), 1.1, { css: { display: "initial" }, ease: Sine.easeOut });
	},
	function () {
		TweenLite.to($(this).find(".modules-div"), 1, { css: { height: "40%", opacity: "1" }, ease: Sine.easeOut });
		TweenLite.to($(this).find(".modules-sub-text"), 0.3, { css: { display: "none" }, ease: Sine.easeOut });
	}
);

$(".hover-sub").hover(
	function () {
		TweenLite.to($(this).find(".hover-div"), 1, { css: { height: "100%", opacity: "0.9" }, ease: Sine.easeOut });
		$('.hover-sub-text p').addClass('t-white p-10');
		TweenLite.to($(this).find(".hover-sub-text"), 1.1, { css: { display: "initial" }, ease: Sine.easeOut });
	},
	function () {
		TweenLite.to($(this).find(".hover-div"), 1, { css: { height: "20%", opacity: "1" }, ease: Sine.easeOut });

		TweenLite.to($(this).find(".hover-sub-text"), 0.3, { css: { display: "none" }, ease: Sine.easeOut });
	}
);

/*  flipbox */
//IE doesn't transform-style:preserve-3d.
// for IE try https://codepen.io/rhernando/pen/vjGxH


//using TweenLite.set() takes care of all vendor-prefixes
TweenLite.set(".cardWrapper", { perspective: 800 });
TweenLite.set(".card", { transformStyle: "preserve-3d" });
TweenLite.set(".back", { rotationY: -180 });
TweenLite.set([".back", ".front"], { backfaceVisibility: "hidden" });

$(".cardWrapper").hover(
	function () {
		TweenLite.to($(this).find(".card"), 1.2, { rotationY: 180, ease: Back.easeOut });
	},
	function () {
		TweenLite.to($(this).find(".card"), 1.2, { rotationY: 0, ease: Back.easeOut });
	}
);

//a nice little intro;)
TweenMax.staggerTo($(".card"), 0.5, { rotationY: -180, repeat: 1, yoyo: true }, 0.1);

$(function () {
	// init controller



	/* new ScrollMagic.Scene({triggerElement: ".timeline"})
					.setTween(timeline_scene)
					.addTo(controller); */


	var scrollController = new ScrollMagic.Controller();

	$(".finbyz-fadeinup").each(function () {
		var fadeUpScene = new ScrollMagic.Scene({
			triggerElement: this,
			triggerHook: 0.8
		})
			.setTween(TweenMax.from(this, 0.8, { y: 50, opacity: 0, ease: Power1.easeIn }))
			.addTo(scrollController)
	})

	$(".finbyz-fadeinup-footer").each(function () {
		var fadeUpScene = new ScrollMagic.Scene({
			triggerElement: this,
			triggerHook: 1
		})
			.setTween(TweenMax.from(this, 0.8, { y: 50, opacity: 0, ease: Power1.easeIn }))
			.addTo(scrollController)
	})

	$(".finbyz-fadeindown").each(function () {
		var fadeUpScene = new ScrollMagic.Scene({
			triggerElement: this,
			triggerHook: 0.8
		})
			.setTween(TweenMax.from(this, 0.8, { y: -50, opacity: 0, ease: Power1.easeIn }))
			.addTo(scrollController)
	})

	$(".finbyz-fadeinleft").each(function () {
		var fadeUpScene = new ScrollMagic.Scene({
			triggerElement: this,
			triggerHook: 0.8
		})
			.setTween(TweenMax.from(this, 0.8, { x: 50, opacity: 0, ease: Power1.easeIn },10))
			.addTo(scrollController)
	})

	$(".finbyz-zoomin").each(function () {
		var fadeUpScene = new ScrollMagic.Scene({
			triggerElement: this,
			triggerHook: 0.8
		})
			.setTween(TweenMax.from(this, 0.8, { scale: 0, ease: Power1.easeIn }))
			.addTo(scrollController)
	})

	$(".card").each(function () {
		var tl_card = new TimelineMax();
		tl_card.to(this, 1.2, { rotationY: 180, ease: Back.easeOut })
			.to(this, 1.2, { rotationY: 0, ease: Back.easeOut, delay: 0.5 });

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
	window.addEventListener("scroll", function () { // or window.addEventListener("scroll"....
		var st = window.pageYOffset || document.documentElement.scrollTop; // Credits: "https://github.com/qeremy/so/blob/master/so.dom.js#L426"
		if (st > lastScrollTop) {
			$('.navbar-main').removeClass('animated swingInX');
			$('.navbar-main').addClass('animated swingOutX');
		} else {
			$('.navbar-main').removeClass('animated swingOutX');
			$('.navbar-main').addClass('animated swingInX');
		}
		lastScrollTop = st <= 0 ? 0 : st; // For Mobile or negative scrolling
	}, false);



});

// for image zoom on hover with fadein effect
$(".hover-zoom").hover(
	function () {
		TweenLite.to(this, 1, { scale:1.05 , ease: Power1.easeIn });
	},
	function () {
		TweenLite.to(this, 1, { scale:1 , ease: Power1.easeIn });
	}
);

// set some global properties
TweenLite.set('.client-grid-wrap', { perspective: 1000 });
TweenLite.set('.client-grid-wrap-inner', { transformStyle: "preserve-3d" });
TweenLite.set('.grid-back', { rotationX: -90 });
TweenLite.set(['.grid-back', '.grid-front'], { backfaceVisibility: "hidden", transformOrigin: '50% 0' });

// loop through each element
$(".client-grid-wrapper").each(function (i, el) {

	// create a timeline for this element in paused state
	var tl = new TimelineMax({ paused: true });

	// create your tween of the timeline in a variable
	var t = tl
		.set(el, { willChange: "transform" })
		.to($(el).find('.client-grid-wrap-inner'), 0.53, { y: "-40px", rotationX: 90, zIndex: 2, overwrite: "all", ease: Back.easeOut }, 0);

	// store the tween timeline in the javascript DOM node
	el.animation = t;

	//create the event handler
	$(el).on("mouseenter", function () {
		this.animation.play();
	}).on("mouseleave", function () {
		this.animation.reverse();
	});

});
var controller = new ScrollMagic.Controller();
function showProjects(tab, delay) {    //return false;
	//$('.project-list.tab-'+tab).addClass('tab-active').show();
	//  $('.filter-item.filter-item--active').removeClass('filter-item--active');
	//   $('.filter-item-'+tab).addClass('filter-item--active');

	$('.project-item').each(function () {
		var $this = this;
		var tween = new TimelineLite()
			.to($(this), 0.5, { css: { className: '+=show' } }, 0.20).delay(Math.floor(Math.random() * (70 + delay - delay) + delay) / 100)
			.from($(this).find('.project-item__details'), 1, { ease: Power4.easeOut, opacity: 0, y: '10%' })
			//.from($(this).find('.icon-arrow-right'), 1, {ease: Power4.easeOut, opacity:0, x: '-20%'}, '-=0.5')
			//.from($(this).find('.project-item__media, .project-item__branding'), 1, {ease: Power4.easeOut, opacity: 0, scale: 0.98, transformOrigin:"50% 50%"}, '-=1.5')
			;

		new ScrollMagic.Scene({
			triggerHook: 1,
			triggerElement: $this
		})

			.addTo(controller)

			//.addIndicators()
			.setTween(tween);
	});

}