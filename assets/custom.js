'use strict';

document.addEventListener('DOMContentLoaded', function () {
  var sidebar = document.getElementsByClassName('sphinxsidebarwrapper')[0];

  (function tweakSidebar() { try {
    var donateH3 = sidebar.querySelector('.donation');
    donateH3.textContent = 'Sponsor';
    var tideliftP = donateH3.nextElementSibling.nextElementSibling;
    var sponsorA = document.createElement('a');
    sponsorA.href = 'https://github.com/sponsors/jab';
    sponsorA.textContent = 'Sponsor bidict on GitHub.'
    sidebar.insertBefore(sponsorA, tideliftP);
    var tideliftH3 = document.createElement('h3');
    tideliftH3.textContent = 'Enterprise';
    tideliftP.innerHTML = 'Enterprise support for bidict is available <a href="https://tidelift.com/subscription/pkg/pypi-bidict?utm_source=pypi-bidict&utm_medium=referral&utm_campaign=docs">via Tidelift</a>.';
    sidebar.insertBefore(tideliftH3, tideliftP);
   } catch (e) {}
  })();

  function addDiv(propName, propVal) {
    var div = document.createElement('div');
    div.style.marginTop = '20px';
    div[propName] = propVal;
    sidebar.append(div);
  }

  function addScript(src) {
    var script = document.createElement('script');
    script.src = src;
    script.async = true;
    document.body.append(script);
  }

  addDiv('className', 'rc-scout');
  addScript('https://www.recurse-scout.com/loader.js?t=c17a917136a40c38f5ce6b80adbbfd19');
});
