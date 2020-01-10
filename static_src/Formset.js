export class Formset {
  constructor(rootEl) {
    this.rootEl = rootEl;
  }
}

export function formsets(selector) {
  let rootEls = document.querySelectorAll(selector);
  rootEls.forEach(rootEl => {
    new Formset(rootEl);
  });
}
