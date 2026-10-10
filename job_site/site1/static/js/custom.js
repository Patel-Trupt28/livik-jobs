/**
Core script to handle the entire theme and core functions
**/

var JobBoard = function(){
	'use strict';
	
	/* Search Bar ============ */
	var screenWidth = $( window ).width();
	
	function getUrlParams(dParam){
		var dPageURL = window.location.search.substring(1),
			dURLVariables = dPageURL.split('&'),
			dParameterName,
			i;

		for (i = 0; i < dURLVariables.length; i++) {
			dParameterName = dURLVariables[i].split('=');

			if (dParameterName[0] === dParam) {
				return dParameterName[1] === undefined ? true : decodeURIComponent(dParameterName[1]);
			}
		}
	}
	
	/* Set Cookies Function */
	function setCookie(cname, cvalue, exhours){
		var d = new Date();
		d.setTime(d.getTime() + (30*60*1000)); /* 30 Minutes */
		var expires = "expires="+ d.toString();
		document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
	}

	/* Get Cookies Function */
	function getCookie(cname) {
		var name = cname + "=";
		var decodedCookie = decodeURIComponent(document.cookie);
		var ca = decodedCookie.split(';');
		for(var i = 0; i <ca.length; i++) {
			var c = ca[i];
			while (c.charAt(0) == ' ') {
				c = c.substring(1);
			}
			if (c.indexOf(name) == 0) {
				return c.substring(name.length, c.length);
			}
		}
		return "";
	}
	
	/* One Page Layout ============ */
	var onePageLayout = function() {
		var headerHeight =   parseInt($('.onepage').css('height'), 10);
		$(".scroll").unbind().on('click',function(event) {
			event.preventDefault();
			
			if (this.hash !== "") {
				var hash = this.hash;	
				var seactionPosition = $(hash).offset().top;
				var headerHeight =   parseInt($('.onepage').css('height'), 10);
				
				
				$('body').scrollspy({target: ".navbar", offset: headerHeight+2}); 
				
				var scrollTopPosition = seactionPosition - (headerHeight);
				
				$('html, body').animate({
					scrollTop: scrollTopPosition
				}, 800, function(){
					
				});
			}   
		});
		if(jQuery(".scroll-bar").length > 0){
			$(".scroll-bar").unbind().on('click',function(event){
				event.preventDefault();
				
				if (this.hash !== "") {
					var hash = this.hash;	
					var seactionPosition = $(hash).offset().top;
					var headerHeight =   parseInt($('.onepage').css('height'), 10);
					
					
					$('body').scrollspy({target: ".navbar", offset: headerHeight+2}); 
					
					var scrollTopPosition = seactionPosition - (headerHeight) + 500;
					
					$('html, body').animate({
						scrollTop: scrollTopPosition
					}, 300, function(){
						
					});
				}   
			});
		}
		$('body').scrollspy({target: ".navbar", offset: headerHeight + 2});  
	}
	
	/* Load File ============ */ 
	
	var dzTheme = function(){
		if(screenWidth <= 991 ){
			jQuery('.navbar-nav > li > a, .sub-menu > li > a').unbind().on('click', function(e){
				//e.preventDefault();
				if(jQuery(this).parent().hasClass('open'))
				{
					jQuery(this).parent().removeClass('open');
				}
				else{
					jQuery(this).parent().parent().find('li').removeClass('open');
					jQuery(this).parent().addClass('open');
				}
			});
		}
	}
	
	/* Magnific Popup ============ */
	var MagnificPopup = function(){
		/* 'use strict'; */	
		/* magnificPopup function */
		jQuery('.mfp-gallery').magnificPopup({
			delegate: '.mfp-link',
			type: 'image',
			tLoading: 'Loading image #%curr%...',
			mainClass: 'mfp-img-mobile',
			gallery: {
				enabled: true,
				navigateByImgClick: true,
				preload: [0,1] // Will preload 0 - before current, and 1 after the current image
			},
			image: {
				tError: '<a href="%url%">The image #%curr%</a> could not be loaded.',
				titleSrc: function(item) {
					return item.el.attr('title') + '<small></small>';
				}
			}
		});
		/* magnificPopup function end */
		
		/* magnificPopup for paly video function */		
		jQuery('.video').magnificPopup({
			type: 'iframe',
			iframe: {
				markup: '<div class="mfp-iframe-scaler">'+
						 '<div class="mfp-close"></div>'+
						 '<iframe class="mfp-iframe" frameborder="0" allowfullscreen></iframe>'+
						 '<div class="mfp-title">Some caption</div>'+
						 '</div>'
			},
			callbacks: {
				markupParse: function(template, values, item) {
					values.title = item.el.attr('title');
				}
			}
		});
		/* magnificPopup for paly video function end*/
		$('.popup-youtube, .popup-vimeo, .popup-gmaps').magnificPopup({
			disableOn: 700,
			type: 'iframe',
			mainClass: 'mfp-fade',
			removalDelay: 160,
			preloader: false,
			fixedContentPos: true
		});
	}
	
	/* Scroll To Top ============ */
	var scrollTop = function (){
		var scrollTop = jQuery("button.scroltop");
		/* page scroll top on click function */	
		scrollTop.on('click',function() {
			jQuery("html, body").animate({
				scrollTop: 0
			}, 1000);
			return false;
		})

		jQuery(window).bind("scroll", function() {
			var scroll = jQuery(window).scrollTop();
			if (scroll > 900) {
				jQuery("button.scroltop").fadeIn(1000);
			} else {
				jQuery("button.scroltop").fadeOut(1000);
			}
		});
		/* page scroll top on click function end*/
	}
	
	/* handle Placeholder ============ */
	var handlePlaceholder = function(){
		/* input placeholder for ie9 & ie8 & ie7 */
		jQuery.support.placeholder = ('placeholder' in document.createElement('input'));
		/* input placeholder for ie9 & ie8 & ie7 end*/
		
		/*fix for IE7 and IE8  */
		if (!jQuery.support.placeholder) {
			jQuery("[placeholder]").focus(function () {
				if (jQuery(this).val() == jQuery(this).attr("placeholder")) jQuery(this).val("");
			}).blur(function () {
				if (jQuery(this).val() == "") jQuery(this).val(jQuery(this).attr("placeholder"));
			}).blur();

			jQuery("[placeholder]").parents("form").submit(function () {
				jQuery(this).find('[placeholder]').each(function() {
					if (jQuery(this).val() == jQuery(this).attr("placeholder")) {
						 jQuery(this).val("");
					}
				});
			});
		}
		/*fix for IE7 and IE8 end */
	}
	
	/* File Input ============ */
	var fileInput = function(){
		/* Input type file jQuery */	 	 
		jQuery(document).on('change', '.btn-file :file', function() {
			var input = jQuery(this);
			var	numFiles = input.get(0).files ? input.get(0).files.length : 1;
			var	label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
			input.trigger('fileselect', [numFiles, label]);
		});
		
		jQuery('.btn-file :file').on('fileselect', function(event, numFiles, label) {
			input = jQuery(this).parents('.input-group').find(':text');
			var log = numFiles > 10 ? numFiles + ' files selected' : label;
		
			if (input.length) {
				input.val(log);
			} else {
				if (log) alert(log);
			}
		});
		/* Input type file jQuery end*/
	}
	
	/* Header Fixed ============ */
	var headerFix = function(){
		/* Main navigation fixed on top  when scroll down function custom */		
		jQuery(window).on('scroll', function () {
			if(jQuery('.sticky-header').length > 0){
				var menu = jQuery('.sticky-header');
				if ($(window).scrollTop() > menu.offset().top) {
					menu.addClass('is-fixed');
				} else {
					menu.removeClass('is-fixed');
				}
			}
		});
		/* Main navigation fixed on top  when scroll down function custom end*/
	}
	
	/* Masonry Box ============ */
	var masonryBox = function(){
		/* masonry by  = bootstrap-select.min.js */
		if(jQuery('#masonry, .masonry').length){
			var self = $("#masonry, .masonry");
			if(jQuery('.card-container').length)
		    {
				self.imagesLoaded(function () {
					self.masonry({
						gutterWidth: 15,
						isAnimated: true,
						itemSelector: ".card-container"
					});
				});
			}
		}
		if(jQuery('.filters').length)
		{
			jQuery(".filters li:first").addClass('active');
			
			jQuery(".filters").on('click','li',function(e) {
				
				jQuery('.filters li').removeClass('active');
				jQuery(this).addClass('active');
				
				e.preventDefault();
				var filter = $(this).attr("data-filter");
				self.masonryFilter({
					filter: function () {
						if (!filter) return true;
						//return $(this).attr("data-filter") == filter;
						return $(this).hasClass(filter);
					}
				});
			});
		}
		/* masonry by  = bootstrap-select.min.js end */
	}
	
	/* Counter Number ============ */
	var counter = function(){
		if(jQuery('.counter').length)
		{
			jQuery('.counter').counterUp({
				delay: 10,
				time: 3000
			});	
		}
	}
	
	/* Video Popup ============ */
	var handleVideo = function(){
		/* Video responsive function */	
		jQuery('iframe[src*="youtube.com"]').wrap('<div class="embed-responsive embed-responsive-16by9"></div>');
		jQuery('iframe[src*="vimeo.com"]').wrap('<div class="embed-responsive embed-responsive-16by9"></div>');	
		/* Video responsive function end */
	}
	
	/* Gallery Filter ============ */
	var handleFilterMasonary = function(){
		/* gallery filter activation = jquery.mixitup.min.js */ 
		if (jQuery('#image-gallery-mix').length) {
			jQuery('.gallery-filter').find('li').each(function () {
				$(this).addClass('filter');
			});
			jQuery('#image-gallery-mix').mixItUp();
		};
		if(jQuery('.gallery-filter.masonary').length){
			jQuery('.gallery-filter.masonary').on('click','span', function(){
				var selector = $(this).parent().attr('data-filter');
				jQuery('.gallery-filter.masonary span').parent().removeClass('active');
				jQuery(this).parent().addClass('active');
				jQuery('#image-gallery-isotope').isotope({ filter: selector });
				return false;
			});
		}
		/* gallery filter activation = jquery.mixitup.min.js */
	}
	
	/* handle Bootstrap Select ============ */
	var handleBootstrapSelect = function(){
		/* Bootstrap Select box function by  = bootstrap-select.min.js */ 
		if (jQuery('select').length) {
		    jQuery('select').selectpicker();
		}
		/* Bootstrap Select box function by  = bootstrap-select.min.js end*/
	}
	
	/* Content Scroll ============ */
	var handleCustomScroll = function(){
		/* all available option parameters with their default values */
		if($(".content-scroll").length > 0)
		{ 
			$(".content-scroll").mCustomScrollbar({
				setWidth:false,
				setHeight:false,
				axis:"y"
			});	
		}
	}
	
	/* WOW ANIMATION ============ */
	var wow_animation = function(){
		if($('.wow').length > 0)
		{
			var wow = new WOW(
			{
			  boxClass:     'wow',      // animated element css class (default is wow)
			  animateClass: 'animated', // animation css class (default is animated)
			  offset:       50,          // distance to the element when triggering the animation (default is 0)
			  mobile:       false       // trigger animations on mobile devices (true is default)
			});
			wow.init();	
		}	
	}
	
	/* Left Menu ============ */
	var handleSideBarMenu = function(){
		$('.openbtn').on('click',function(e){
			e.preventDefault();
			if($('#mySidenav').length > 0)
			{
				document.getElementById("mySidenav").style.left = "0";
			}

			if($('#mySidenav1').length > 0)
			{
				document.getElementById("mySidenav1").style.right = "0";
			}
			
		})
		
		$('.closebtn').on('click',function(e){
			e.preventDefault();
			if($('#mySidenav').length > 0)
			{
				document.getElementById("mySidenav").style.left = "-300px";
			}
			
			if($('#mySidenav1').length > 0)
			{
				document.getElementById("mySidenav1").style.right = "-820px";
			}
		})
	}
	
	/* Left Menu ============ */
	var handleMenuPosition = function(){
		$(".header-nav li").unbind().each(function (e) {
			if ($('ul', this).length) {
				var elm = $('ul:first', this);
				var off = elm.offset();
				var l = off.left;
				var w = elm.width();
				var docH = $("body").height();
				var docW = $("body").width();

				var isEntirelyVisible = (l + w <= docW);

				if (!isEntirelyVisible) {
					$(this).find('.sub-menu:first').addClass('left');
				} else {
					$(this).find('.sub-menu:first').removeClass('left');
				}
			}
		});
	}	
	
	var reposition = function (){
		var modal = jQuery(this),
		dialog = modal.find('.modal-dialog');
		modal.css('display', 'block');
		
		/* Dividing by two centers the modal exactly, but dividing by three or four works better for larger screens.  */
		dialog.css("margin-top", Math.max(0, (jQuery(window).height() - dialog.height()) / 2));
	}
	
	var handlePlaceholderAnimation = function(){
		if(jQuery('.dezPlaceAni').length){
			$('input, textarea').focus(function(){
				$(this).parents('.form-group').addClass('focused');
			});
			$('input, textarea').blur(function(){
			  var inputValue = $(this).val();
			  if ( inputValue == "" ) {
				$(this).removeClass('filled');
				$(this).parents('.form-group').removeClass('focused');  
			  } else {
				$(this).addClass('filled');
			  }
			})
		}
	}
	
	// Repeater
	var handleRepeater = function (){
		if(jQuery('.repeater').length){
			$('.repeater').repeater({
				repeaters: [{
					selector: '.inner-repeater'
				}]
			});	
		}
	}
	
	// Tags Input
	var handletagsInput = function (){
		if(jQuery('.tags_input').length)
		{
			var data = [
				'css',
				'HTML',
				'php',
				'jquery'
			];

			$(".tags_input").tagComplete({
				keylimit: 1,
				hide: false,
				autocomplete: {
					data: data
				}
			});
		}
	}
	
	// Nav Link
	var handletagsInput = function (){
		if(jQuery('.nav-link').length)
		{
			jQuery('.nav-link').on('click',function(){
				jQuery('.nav-link').removeClass('active');
				jQuery(this).addClass('active');
			});
		}
	}
	
	// Select All Checkbox
	var handleSelectAllCheck = function (){
		if(jQuery('.selectAllCheckBox').length)
		{
			$('.selectAllCheckBox').click(function(e){
				var table= $(e.target).closest('table');
				$('td input:checkbox',table).prop('checked',this.checked);
			});
		}
	}
	
	// Light Gallery
	var lightGallery = function (){
		if(($('#lightgallery, .lightgallery').length > 0)){
			$('#lightgallery, .lightgallery').lightGallery({
				selector : '.lightimg',
				loop:true,
				thumbnail:true,
				exThumbImage: 'data-exthumbimage',
				download: false,
				share: false,
			});
		}
	}	
	
	var handleSupport = function () {
		// Support widget disabled to prevent third-party popups.
	}
	
	// handleDarkTheme
	var handleDarkTheme = function (){
		
		/* Light-Dark Theme Version Button Setting For JobBoard */
		/* Theme Version */	
		var version =  getUrlParams('version');
		
		if(version === undefined)
		{
			var version = getCookie('version');
		}
		
		
		if(version == 'dark'){
			jQuery('.layout-btn').addClass('active');
			jQuery('.layout-btn input').attr('checked', 'checked');
			jQuery('body').addClass('layout-dark');
		}else{
			jQuery('.layout-btn').removeClass('active');
			jQuery('body').removeClass('layout-dark');
			jQuery('.layout-btn input').removeAttr('checked', 'checked');
		}
		
		/* Theme Layout button */
		if(jQuery('.layout-btn').length && window.CinemaTheme){
			// Delegated to unified CinemaTheme engine
		} else if(false){
			jQuery('.light-theme').on('click', function(){
				jQuery('.layout-btn').removeClass('active');
				jQuery('.layout-btn input').removeAttr('checked', 'checked');
			});
			jQuery('.dark-theme').on('click', function(){
				jQuery('.layout-btn').addClass('active');
				jQuery('.layout-btn input').attr('checked', 'checked');
			});
		}
	}
	
	var handleCurrentActive = function() {
		for (var nk = window.location,
			o = $(".header-nav .navbar-nav a").filter(function() {
				return this.href == nk;
			})
			.addClass("active")
			.parent()
			.addClass("active");;) 
		{
			
			if (!o.is("li")) break;
			
			o = o.parent()
				.addClass("mm-show")
				.parent()
				.addClass("active");
		}
	}
	
	/* Handle Navbar Toggler ============ */
	var handleScreenLock = function(){
		jQuery('.navbar-toggler').on('click',function(){
			jQuery('body').toggleClass('screen-lock');
			jQuery('.styleswitcher').toggleClass('hide');
		});
	}
	
	/* Function ============ */
	return {
		init:function(){
			wow_animation();
			onePageLayout();
			dzTheme();
			MagnificPopup();
			scrollTop();
			handlePlaceholder();
			handlePlaceholderAnimation();
			fileInput();
			handleVideo();
			handleFilterMasonary();
			handleSideBarMenu();
			headerFix();
			handleDarkTheme();
			handleRepeater();
			handletagsInput();
			lightGallery();
			handleSelectAllCheck();
			handleSupport();
			jQuery('.modal').on('show.bs.modal', reposition);
			$('[data-bs-toggle="tooltip"]').tooltip()
			handleCurrentActive();
			handleScreenLock();
		},
		
		
		load:function(){
			handleBootstrapSelect();
			counter();
			handleMenuPosition();
			masonryBox();
			handleCustomScroll();
			 
		},
		
		resize:function(){
			screenWidth = $(window).width();
			dzTheme();
			handleSideBarMenu();
			handleMenuPosition();
		}
	}
	
}();

/* Document.ready Start */	
jQuery(document).ready(function() {
  
	JobBoard.init();
	
	jQuery('.navicon').on('click',function(){
		$(this).toggleClass('open');
	});

	$('a[data-bs-toggle="tab"]').click(function(){
		// todo remove snippet on bootstrap v4
		$('a[data-bs-toggle="tab"]').click(function() {
		  $($(this).attr('href')).show().addClass('show active').siblings().hide();
		})
	 });
	
});
/* Document.ready END */

/* Window Load START */
jQuery(window).on("load", function (e) {
	JobBoard.load();
	 setTimeout(function(){
		jQuery('#loading-area').remove();
	}, 0);
	
});
/*  Window Load END */

/* Window Resize START */
jQuery(window).on('resize',function () {
	'use strict'; 
	JobBoard.resize();
});
