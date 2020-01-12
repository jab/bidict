'use strict';

document.addEventListener('DOMContentLoaded', function () {
  var sidebar = document.getElementsByClassName('sphinxsidebarwrapper')[0];

  (function tweakSidebar() { try {
    var donateH3 = sidebar.querySelector('.donation');
    donateH3.textContent = 'Giving back';
    var tideliftP = donateH3.nextElementSibling.nextElementSibling;
    var givebackA = document.createElement('a');
    givebackA.href = 'https://gumroad.com/l/bidict';
    givebackA.textContent = 'Bidict is the product of hundreds of hours of unpaid, voluntary work. If bidict has helped you accomplish your work, click here to chip in toward the costs of bidict’s maintenance and development.'
    sidebar.insertBefore(givebackA, tideliftP);
    var tideliftH3 = document.createElement('h3');
    tideliftH3.textContent = 'Get Support';
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
