/**
 * Livik Jobs - Dashboard Responsive Drawer & Mobile Interaction Controller
 */
document.addEventListener('DOMContentLoaded', function () {
  'use strict';

  var burger = document.querySelector('.burger-icon');
  var mobileNav = document.querySelector('.mobile-header-active');

  // Ensure body overlay exists
  var overlay = document.querySelector('.body-overlay-1');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'body-overlay-1';
    document.body.appendChild(overlay);
  }

  function openDashboardMenu() {
    if (burger) burger.classList.add('burger-close');
    if (mobileNav) mobileNav.classList.add('sidebar-visible');
    document.body.classList.add('mobile-menu-active');
    overlay.style.visibility = 'visible';
    overlay.style.opacity = '1';
  }

  function closeDashboardMenu() {
    if (burger) burger.classList.remove('burger-close');
    if (mobileNav) mobileNav.classList.remove('sidebar-visible');
    document.body.classList.remove('mobile-menu-active');
    overlay.style.visibility = 'hidden';
    overlay.style.opacity = '0';
  }

  if (burger) {
    burger.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (mobileNav && mobileNav.classList.contains('sidebar-visible')) {
        closeDashboardMenu();
      } else {
        openDashboardMenu();
      }
    });
  }

  overlay.addEventListener('click', closeDashboardMenu);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeDashboardMenu();
  });

  // Auto-close on link navigation
  if (mobileNav) {
    var links = mobileNav.querySelectorAll('a');
    links.forEach(function (link) {
      link.addEventListener('click', function () {
        closeDashboardMenu();
      });
    });
  }

  // Handle window resize
  window.addEventListener('resize', function () {
    if (window.innerWidth >= 1200) {
      closeDashboardMenu();
    }
  });
});
