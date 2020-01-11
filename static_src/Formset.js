/**
 * Formset management
 */

class Form {
  /**
   * Track forms within a formset
   */
  constructor(rootEl, prefix) {
    this.rootEl = rootEl;
    this.prefix = prefix;

    this.deleteEl = `${prefix}-DELETE`;
  }

  get isDeleted() {
    return this.deleteEl.checked;
  }

  delete() {
    if (this.isDeleted) {
      return;
    }
    this.deleteEl.checked = false;
  }

  undelete() {
    if (!this.isDeleted) {
      return;
    }
    this.deleteEl.checked = true;
  }
}

export class Formset {
  /**
   * Manage a formset
   */
  constructor(
    rootEl,
    prefix,
    dataForm='fastview-formset-form',
    dataTemplate='fastview-formset-template',
  ) {
    this.rootEl = rootEl;
    this.prefix = prefix;

    // Find management form
    this.total_forms = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    this.initial_forms = document.getElementById(`id_${prefix}-INITIAL_FORMS`);
    this.min_num_forms = document.getElementById(`id_${prefix}-MIN_NUM_FORMS`);
    this.max_num_forms = document.getElementById(`id_${prefix}-MAX_NUM_FORMS`);

    // Find existing forms
    let formEls = rootEl.querySelectorAll(`[data-${dataForm}]`);
    this.forms = []
    formEls.forEach(formEl => {
      let formPrefix = formEl.dataset[dataForm];
      let form = new Form(formEl, formPrefix);
      this.forms.push(form);
    });

    // Find template form
    this.template = rootEl.querySelector(`[data-${dataTemplate}]`);
  }
}

export function formsets(
  dataFormset='fastview-formset',
  dataForm='fastview-formset-form',
  dataTemplate='fastview-formset-template',
) {
  /**
   * Initialise formsets with the data attribute matching dataFormset
   */
  let rootEls = document.querySelectorAll(`[data-${dataFormset}]`);
  rootEls.forEach(rootEl => {
    let prefix = rootEl.dataset[dataFormset];
    new Formset(rootEl, prefix, dataForm, dataTemplate);
  });
}
