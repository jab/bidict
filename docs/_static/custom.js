'use strict';

document.addEventListener('DOMContentLoaded', function() {
  function addScript(src) {
    var el = document.createElement('script');
    el.setAttribute('async', '');
    el.setAttribute('src', src);
    document.head.appendChild(el);
  }
  // Google Analytics
  addScript('https://www.googletagmanager.com/gtag/js?id=UA-10116163-3');
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', 'UA-10116163-3');

  var sidebarUl = document.querySelector('.sidebar-tree > ul');
  sidebarUl.insertAdjacentHTML('beforeend', '<li class="toctree l1"><a class="reference external" href="https://github.com/jab/bidict">GitHub Repository</a></li>');
  sidebarUl.insertAdjacentHTML('afterend', '<div><img src="https://static.scarf.sh/a.png?x-pxid=15b5b7c1-9453-4ab6-8a82-8cfa0f4db4f9" /></div>')
});
