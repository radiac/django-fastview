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
  constructor(formset, rootEl, prefix) {
    this.formset = formset;
    this.rootEl = rootEl;
    this.prefix = prefix;

    this.deleteEl = this.getDeleteEl();
    this.deleteCon = this.getDeleteCon();
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

  getDeleteCon() {
    return this.deleteEl.parentNode;
  }

  get isDeleted() {
    return this.deleteEl.checked;
  }

  deleted() {
    this.formset.deletedForm(this);
  }

  undeleted() {
    this.formset.addedForm(this);
  }

  formsetChanged() {
    this.render();
  }

  render() {
    /**
     * Render the form whenever there is a change to delete state
     *
     * Hides and shows the delete field
     */
    if (this.formset.canDelete) {
      this.deleteCon.style.removeProperty('display');
    } else {
      this.deleteCon.style.setProperty('display', 'none');
    }
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
    this.totalFormsEl = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    this.initialForms = document.getElementById(`id_${prefix}-INITIAL_FORMS`);
    this.numFormsMin = parseInt(document.getElementById(`id_${prefix}-MIN_NUM_FORMS`).value, 10);
    this.numFormsMax = parseInt(document.getElementById(`id_${prefix}-MAX_NUM_FORMS`).value, 10);
    this.numFormsMin = 3
    this.numFormsMax = 5

    this.nextId = this.numForms + 1;

    // Find existing forms
    let formEls = rootEl.querySelectorAll(`[data-${this.dataForm}]`);
    this.forms = []
    formEls.forEach(formEl => {
      let formPrefix = formEl.getAttribute(`data-${this.dataForm}`);
      let form = new this.formClass(this, formEl, formPrefix);
      this.forms.push(form);
    });

    // Find template form
    this.template = rootEl.querySelector(`[data-${this.dataTemplate}]`);
    this.templatePrefix = this.template.getAttribute(`data-${this.dataTemplate}`);

    // Find add button
    this.addEl = this.getAddEl();
    this.addCon = this.getAddCon();

    // Re-render this and all forms
    this.render();
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
  }

  getAddCon() {
    return this.addEl;
  }

  addForm() {
    /**
     * Create and insert a new form, and let all forms know the formset has changed
     */
    // Get new form ID
    let id = this.nextId;

    // Create and insert
    let formRoot = this.createForm(id);
    let newForm = this.insertForm(id, formRoot);

    // Notify handlers
    this.addedForm(newForm);
  }

  render() {
    /**
     * Re-render formset and forms
     */
    this.forms.forEach(form => {
      form.formsetChanged();
    });

    if (this.canAdd) {
      this.addCon.style.removeProperty('display');
    } else {
      this.addCon.style.setProperty('display', 'none');
    }
  }

  get numForms() {
    return parseInt(this.totalFormsEl.value, 10)
  }

  set numForms(value) {
    this.totalFormsEl.value = value;
  }

  createForm(id) {
    /**
     * Create a new form
     */
    // Clone template, replacing __prefix__
    let template = this.template.innerHTML;
    let formHtml = template.replace(/__prefix__/g, id);
    let formRoot = this.template.cloneNode();
    formRoot.removeAttribute("style");
    formRoot.innerHTML = formHtml;

    return formRoot
  }

  insertForm(id,formRoot) {
    /**
     * Insert the new form into the formset
     */
    // Add to the end of the existing forms, or after the template if no forms yet
    let lastForm = this.template;
    if (this.forms.length > 0) {
      lastForm = this.forms[this.forms.length - 1].rootEl;
    }
    lastForm.parentNode.insertBefore(formRoot, lastForm.nextSibling);

    // Register form
    let newPrefix = this.templatePrefix.replace('__prefix__', id)
    let form = new Form(this, formRoot, newPrefix)
    this.forms.push(form);
    return form;
  }

  addedForm(form) {
    /**
     * Called when the form has been added to the formset
     *
     * Hides and shows the add button
     */
    this.numForms += 1
    this.render();
  }

  deletedForm(form) {
    this.numForms -= 1
    this.render();
  }

  get canAdd() {
    /**
     * Can add if the limit has not been reached
     */
    return this.numForms < this.numFormsMax;
  }

  get canDelete() {
    /**
     * Can delete if there are more than the minimum number
     */
    return this.numForms > this.numFormsMin;
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
