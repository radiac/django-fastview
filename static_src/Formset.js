/**
 * Formset management
 */

const defaultDataFormset = 'fastview-formset';
const defaultDataForm = 'fastview-formset-form';
const defaultDataTemplate = 'fastview-formset-template';


class Form {
  /**
   * Track forms within a formset
   */
  constructor(rootEl, prefix) {
    this.rootEl = rootEl;
    this.prefix = prefix;

    this.deleteEl = this.getDeleteEl();
    this.render();
  }

  getDeleteEl() {
    let checkbox = this.rootEl.querySelector(`[name="${this.prefix}-DELETE"]`);
    checkbox.onchange = () => {
      if (checkbox.checked) {
        this.deleted();
      } else {
        this.undeleted();
      }
    };
    return checkbox
  }

  get isDeleted() {
    return this.deleteEl.checked;
  }

  delete() {
    if (this.isDeleted) {
      return;
    }
    this.deleteEl.checked = false;
    this.deleted();
  }

  deleted() {
    this.render();
  }

  undelete() {
    if (!this.isDeleted) {
      return;
    }
    this.deleteEl.checked = true;
    this.undeleted();
  }

  undeleted() {
    this.render();
  }

  render() {
    /**
     * Render the form whenever there is a change to delete state
     *
     * Placeholder to allow subclasses to control display of delete button and state
     */
  }
}

export class Formset {
  /**
   * Manage a formset
   */

  dataForm = defaultDataForm;
  dataTemplate = defaultDataTemplate;
  formClass = Form;

  constructor(rootEl, prefix) {
    this.rootEl = rootEl;
    this.prefix = prefix;

    // Find management form
    this.total_forms = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    this.initial_forms = document.getElementById(`id_${prefix}-INITIAL_FORMS`);
    this.min_num_forms = document.getElementById(`id_${prefix}-MIN_NUM_FORMS`);
    this.max_num_forms = document.getElementById(`id_${prefix}-MAX_NUM_FORMS`);

    // Find existing forms
    let formEls = rootEl.querySelectorAll(`[data-${this.dataForm}]`);
    this.forms = []
    formEls.forEach(formEl => {
      let formPrefix = formEl.getAttribute(`data-${this.dataForm}`);
      let form = new this.formClass(formEl, formPrefix);
      this.forms.push(form);
    });

    // Find template form
    this.template = rootEl.querySelector(`[data-${this.dataTemplate}]`);
    this.templatePrefix = this.template.getAttribute(`data-${this.dataTemplate}`);

    // Find and show add button
    this.addEl = this.getAddEl();
  }

  getAddEl() {
    let button = document.createElement('button');
    button.innerHTML = 'Add';
    button.type = 'button';
    this.rootEl.appendChild(button);
    button.onclick = () => {
      this.addForm();
    }
    return button;
  };

  addForm() {
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

export function formsets(dataFormset = defaultDataFormset) {
  /**
   * Initialise formsets with the data attribute matching dataFormset
   */
  let rootEls = document.querySelectorAll(`[data-${dataFormset}]`);
  rootEls.forEach(rootEl => {
    let prefix = rootEl.getAttribute(`data-${dataFormset}`);
    new Formset(rootEl, prefix);
  });
}
