/**
 * Livik Jobs - Responsive Navigation & Drawer Controller
 * Handles mobile hamburger toggling, animated backdrop, touch sub-menus, and auto-closing.
 */
document.addEventListener('DOMContentLoaded', function () {
  'use strict';

  var toggler = document.querySelector('.navbar-toggler');
  var navCollapse = document.getElementById('navbarNavDropdown');
  var header = document.querySelector('.site-header');

  if (!toggler || !navCollapse) return;

  // Create or select backdrop
  var backdrop = document.querySelector('.mobile-nav-backdrop');
  if (!backdrop) {
    backdrop = document.createElement('div');
    backdrop.className = 'mobile-nav-backdrop';
    document.body.appendChild(backdrop);
  }

  function openMenu() {
    navCollapse.classList.add('show');
    toggler.classList.add('open');
    toggler.setAttribute('aria-expanded', 'true');
    backdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeMenu() {
    navCollapse.classList.remove('show');
    toggler.classList.remove('open');
    toggler.setAttribute('aria-expanded', 'false');
    backdrop.classList.remove('active');
    document.body.style.overflow = '';
  }

  toggler.addEventListener('click', function (e) {
    e.stopPropagation();
    if (navCollapse.classList.contains('show')) {
      closeMenu();
    } else {
      openMenu();
    }
  });

  backdrop.addEventListener('click', closeMenu);

  // Close menu when escape key pressed
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && navCollapse.classList.contains('show')) {
      closeMenu();
    }
  });

  // Handle dropdown / submenu clicks on mobile
  var navLinks = navCollapse.querySelectorAll('.nav.navbar-nav > li > a');
  navLinks.forEach(function (link) {
    var parentLi = link.parentElement;
    var subMenu = parentLi.querySelector('.sub-menu');

    if (subMenu) {
      link.addEventListener('click', function (e) {
        if (window.innerWidth <= 991) {
          e.preventDefault();
          e.stopPropagation();
          var isOpen = parentLi.classList.contains('open');

          // Close other open submenus
          navCollapse.querySelectorAll('.nav.navbar-nav > li.open').forEach(function (openLi) {
            if (openLi !== parentLi) openLi.classList.remove('open');
          });

          if (!isOpen) {
            parentLi.classList.add('open');
          } else {
            parentLi.classList.remove('open');
          }
        }
      });
    } else {
      // Normal navigation link: close drawer upon click
      link.addEventListener('click', function () {
        if (window.innerWidth <= 991) {
          closeMenu();
        }
      });
    }
  });

  // Also close menu on sub-menu link clicks
  var subMenuLinks = navCollapse.querySelectorAll('.sub-menu a');
  subMenuLinks.forEach(function (subLink) {
    subLink.addEventListener('click', function () {
      if (window.innerWidth <= 991) {
        closeMenu();
      }
    });
  });

  // Window resize reset
  window.addEventListener('resize', function () {
    if (window.innerWidth > 991 && navCollapse.classList.contains('show')) {
      closeMenu();
    }
  });
});
