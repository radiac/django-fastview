/**
 * Formset management
 */

const defaultDataFormset = 'fastview-formset';
const defaultDataForm = 'fastview-formset-form';
const defaultDataTemplate = 'fastview-formset-template';

const addButton = (formset) => {
  let button = document.createElement('button');
  button.innerHTML = 'Add';
  button.type = 'button';
  formset.rootEl.appendChild(button);
  return button;
};

class Form {
  /**
   * Track forms within a formset
   */
  constructor(rootEl, prefix) {
    this.rootEl = rootEl;
    this.prefix = prefix;

    this.deleteEl = rootEl.querySelector(`[name="${prefix}-DELETE"]`);
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
    dataForm=defaultDataForm,
    dataTemplate=defaultDataTemplate,
    getAddButton=addButton,
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
      let formPrefix = formEl.getAttribute(`data-${dataForm}`);
      let form = new Form(formEl, formPrefix);
      this.forms.push(form);
    });

    // Find template form
    this.template = rootEl.querySelector(`[data-${dataTemplate}]`);
    this.templatePrefix = this.template.getAttribute(`data-${dataTemplate}`);

    // Find and show add button
    this.addButton = getAddButton(this);
    this.addButton.onclick = () => {
      this.add();
    }
  }

  add() {
    // Get new form ID
    let id = parseInt(this.total_forms.value, 10);
    id += 1;
    this.total_forms.value = id;

    // Clone template, replacing __prefix__
    let template = this.template.innerHTML;
    let formHtml = template.replace(/__prefix__/g, id);
    let formRoot = this.template.cloneNode();
    formRoot.removeAttribute("style");
    formRoot.innerHTML = formHtml;

    // Add to the end of the existing forms, or after the template if no forms yet
    let lastForm = this.template;
    if (this.forms.length > 0) {
      lastForm = this.forms[this.forms.length - 1].rootEl;
    }
    lastForm.parentNode.insertBefore(formRoot, lastForm.nextSibling);

    // Register form
    let newPrefix = this.templatePrefix.replace('__prefix__', id)
    let form = new Form(formRoot, newPrefix)
    this.forms.push(form);
  }
}

export function formsets(
  dataFormset=defaultDataFormset,
  dataForm=defaultDataForm,
  dataTemplate=defaultDataTemplate,
  getAddButton=addButton,
) {
  /**
   * Initialise formsets with the data attribute matching dataFormset
   */
  let rootEls = document.querySelectorAll(`[data-${dataFormset}]`);
  rootEls.forEach(rootEl => {
    let prefix = rootEl.getAttribute(`data-${dataFormset}`);
    new Formset(rootEl, prefix, dataForm, dataTemplate, getAddButton);
  });
}
