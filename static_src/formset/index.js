/**
 * Formset management
 */

const defaultDataFormset = 'fastview-formset';
const defaultDataForm = 'fastview-formset-form';
const defaultDataTemplate = 'fastview-formset-template';
const defaultDataPk = 'fastview-formset-pk';

class Form {
  /**
   * Track forms within a formset
   */
  constructor(formset, rootEl, prefix) {
    this.formset = formset;
    this.rootEl = rootEl;
    this.prefix = prefix;

    // Set a flag so CSS can change its layout
    this.rootEl.classList.add("js-enabled");

    this.deleteEl = this.getDeleteEl();
    this.deleteCon = this.getDeleteCon();
    this.render();
  }

  isExtra(fieldDefaults, pkName) {
    /**
     * Check if this is an extra form which can be removed on page load
     *
     * Extra forms have the same values as the template, and have no ID
     */

    // See if all field elements are empty (default)
    const fields = Array.from(this.rootEl.querySelectorAll('input, select, textarea'));
    const hasContent = fields.some(
      fieldEl => {
        // Return true if the field has a non-default value
        const fieldName = fieldEl.name.replace(`${this.prefix}-`, '');
        if (fieldName == pkName && fieldEl.value) {
          // PK is set
          return true;
        }
        if (fieldName in fieldDefaults && fieldEl.value == fieldDefaults[fieldName]) {
          // Field is known and value is default
          return false;
        };
        // Unexpected value
        return true;
      }
    );
    // We're checking if it's empty
    return !hasContent;
  }

  getDeleteEl() {
    let checkbox = this.rootEl.querySelector(`[name="${this.prefix}-DELETE"]`);
    if (!checkbox) {
      return;
    }

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
    if (!this.deleteEl) {
      return;
    }
    return this.deleteEl.parentNode;
  }

  get isDeleted() {
    return this.deleteEl.checked;
  }

  deleted() {
    /**
     * Notify the formset that the form has been deleted
     */
    this.formset.deletedForm(this);
  }

  undeleted() {
    /**
     * Notify the formset that the form has been added
     */
    this.formset.addedForm(this);
  }

  formsetChanged() {
    this.render();
  }

  render() {
    /**
     * Render the form whenever there is a change to delete state
     */
    if (!this.deleteCon) {
      return;
    }

    // Update root style for CSS
    this.rootEl.classList.toggle("deleted", this.isDeleted);

    // Show or hide the delete button
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
  dataPk = defaultDataPk;
  formClass = Form;

  constructor(rootEl, prefix) {
    this.rootEl = rootEl;
    this.prefix = prefix;

    // Find management form
    this.totalFormsEl = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    this.initialFormsEl = document.getElementById(`id_${prefix}-INITIAL_FORMS`);
    this.numFormsMin = parseInt(document.getElementById(`id_${prefix}-MIN_NUM_FORMS`).value, 10);
    this.numFormsMax = parseInt(document.getElementById(`id_${prefix}-MAX_NUM_FORMS`).value, 10);

    // Collect other metadata
    const pkName = rootEl.getAttribute(`data-${this.dataPk}`);

    // Find template form
    this.template = rootEl.querySelector(`[data-${this.dataTemplate}]`);
    this.templatePrefix = this.template.getAttribute(`data-${this.dataTemplate}`);

    // Find existing forms; reverse them so we can discard empty from the end
    const formEls = Array.from(
      rootEl.querySelectorAll(`[data-${this.dataForm}]`)
    ).reverse();

    // Update total number of forms - this may have changed if the page wsa refreshed
    this.numForms = formEls.length;

    // We're removing if we have empty extra forms
    const initialForms = parseInt(this.initialFormsEl.value, 10);
    let removing = (this.numForms > initialForms);

    // Build list of template fields so we can see which values have changed
    const fieldDefaults = {};
    if (removing) {
      Array.from(this.template.querySelectorAll('input, select, textarea')).forEach(
        fieldEl => {
          const fieldName = fieldEl.name.replace(`${this.templatePrefix}-`, '');
          fieldDefaults[fieldName] = fieldEl.value;
        }
      );
    }

    // Build list of form class instances for active forms
    this.forms = []
    formEls.forEach(formEl => {
      let formPrefix = formEl.getAttribute(`data-${this.dataForm}`);
      let form = new this.formClass(this, formEl, formPrefix);

      // Try to remove extra empty forms from the end
      if (removing) {
        if (form.isExtra(fieldDefaults, pkName)) {
          formEl.remove();
          this.numForms -= 1;

          formEl.dispatchEvent(
            new CustomEvent(
              'fastview-formset-destroyForm',
              {bubbles: true, detail: {formset: this, form: form}},
            )
          );
          return;
        }
      }

      // Keep
      this.forms.push(form);
    });
    this.forms.reverse();

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
    button.className = 'fastview-add';
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

    formRoot.dispatchEvent(
      new CustomEvent(
        'fastview-formset-createForm',
        {bubbles: true, detail: {formset: this, form: newForm}},
      )
    );
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

  get nextId() {
    // Forms are 0-indexed, so last ID is num-1
    return this.numForms;
  }

  createForm(id) {
    /**
     * Create a new form
     */
    // Clone template, replacing __prefix__
    let template = this.template.innerHTML;
    let formHtml = template.replace(/__prefix__/g, id);
    let formRoot = this.template.cloneNode();

    formRoot.classList.add('added');
    formRoot.removeAttribute("style");
    formRoot.innerHTML = formHtml;

    return formRoot
  }

  insertForm(id, formRoot) {
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
    form.rootEl.dispatchEvent(
      new CustomEvent(
        'fastview-formset-addForm',
        {bubbles: true, detail: {formset: this, form: form}},
      )
    );
  }

  deletedForm(form) {
    form.rootEl.dispatchEvent(
      new CustomEvent(
        'fastview-formset-deleteForm',
         {bubbles: true, detail: {formset: this, form: form}},
      )
    );
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

export function formsets(
  dataFormset = defaultDataFormset,
  formsetClass = Formset,
) {
  /**
   * Initialise formsets with the data attribute matching dataFormset
   */
  let rootEls = document.querySelectorAll(`[data-${dataFormset}]`);
  rootEls.forEach(rootEl => {
    let prefix = rootEl.getAttribute(`data-${dataFormset}`);
    new formsetClass(rootEl, prefix);
  });
}
