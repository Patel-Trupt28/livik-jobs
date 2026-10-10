/* JavaScript Document */
jQuery(document).ready(function() {
    'use strict';
		
	/*  Blog post Carousel function by = owl.carousel.js */
	jQuery('.blog-carousel').owlCarousel({
		loop:true,
		autoplay:true,
		margin:30,
		nav:true,
		dots: false,
		navText: ['<i class="ti-angle-left"></i>', '<i class="ti-angle-right"></i>'],
		responsive:{
			0:{
				items:1
			},
			480:{
				items:2
			},			
			991:{
				items:2
			},
			1000:{
				items:3
			}
		}
	})
	
	/*  Blog post Carousel function by = owl.carousel.js */
	jQuery('.blog-carousel-center').owlCarousel({
		loop:true,
		center:true,
		autoplay:true,
		margin:30,
		nav:true,
		dots: false,
		navText: ['<i class="ti-angle-left"></i>', '<i class="ti-angle-right"></i>'],
		responsive:{
			0:{
				items:1
			},
			480:{
				items:2
			},			
			991:{
				items:2
			},
			1000:{
				items:3
			}
		}
	})

	/*  Our partners function by = owl.carousel.js */
	jQuery('.our-partners').owlCarousel({
		//center: true,
		autoplay:true,
		loop:true,
		margin:30,
		nav:false,
		dots:true,
		autoplaySpeed: 1000,
		navSpeed: 1000,
		paginationSpeed: 1000,
		slideSpeed: 1000,
		navText: ['<i class="ti-angle-left"></i>', '<i class="ti-angle-right"></i>'],
		responsive:{
			0:{
				items:1
			},
			
			480:{
				items:1
			},				
			500:{
				items:3 
			},	
			767:{
				items:3
			},
			991:{
				items:4
			},
			1000:{
				items:6
			}
		}
	})
	
	/*  Reviews Testimonial function by = owl.carousel.js */
	jQuery('.review-testimonial').owlCarousel({
		//center: true,
		autoplay:true,
		loop:true,
		margin:20,
		nav:false,
		dots:true,
		autoplaySpeed: 1000,
		navSpeed: 1000,
		paginationSpeed: 1000,
		slideSpeed: 1000,
		navText: ['<i class="ti-angle-left"></i>', '<i class="ti-angle-right"></i>'],
		responsive:{
			0:{
				items:1
			},
			480:{
				items:1
			},
			767:{
				items:1
			},	
			768:{
				items:2
			},	
			1199:{
				items:2
			},
			1200:{
				items:3
			}
		}
	})
	
});
/* Document .ready END */