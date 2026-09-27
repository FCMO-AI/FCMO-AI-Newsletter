(function () {
  'use strict';
  var button = document.querySelector('.menu-toggle');
  var navigation = document.querySelector('.site-navigation');
  if (!button || !navigation) return;
  button.addEventListener('click', function () {
    var open = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', String(!open));
    navigation.classList.toggle('is-open', !open);
  });
}());
