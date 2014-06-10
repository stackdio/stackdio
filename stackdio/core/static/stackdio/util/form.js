define(function () {
    return {
        clearForm: function (id) {
            var i, form = document.getElementById(id), elements = form.elements;

            for (i = 0; i < elements.length; i++) {
                field_type = elements[i].type.toLowerCase();
                switch (field_type) {
                case "text":
                case "password":
                case "textarea":
                case "hidden":
                    elements[i].value = "";
                    break;
                case "number":
                    elements[i].value = NaN;
                    break;
                case "radio":
                case "checkbox":
                    if (elements[i].checked) {
                        elements[i].checked = false;
                    }
                    break;
                case "select-one":
                case "select-multi":
                    elements[i].selectedIndex = -1;
                    break;
                default:
                    break;
                }
            }
        },
        collectFormFields: function (obj) {
            var i, item, el, form = {}, id, idx;
            var o, option, options, selectedOptions;

            // Collect the fields from the form
            for (i = 0; i < obj.elements.length; ++i) {
                item = obj.elements[i];
                if(item !== null) {
                  field_type = item.type.toLowerCase();
                    id = item.id;
                    form[id] = {};

                    switch (field_type) {
                        case 'textarea':
                            form[id].text = item.text;
                            form[id].value = item.value;
                            break;
                        case 'checkbox':
                            form[id].text = '';
                            form[id].value = item.checked;
                            break;
                        case 'hidden':
                        case 'text':
                            if (item.files === null) {
                                form[id].text = item.text;
                                form[id].value = item.value;
                            }
                            else {
                                form[id].text = '';
                                form[id].value = '';
                                form[id].files = item.files;
                            }
                            break;
                        case 'number':
                            form[id].text = item.text;
                            form[id].value = parseInt(item.value);
                            break;
                        case 'select-one':
                        case 'select-multi':
                        case 'select-multiple':
                            el = document.getElementById(id);

                            if (el.multiple) {
                                form[id] = [];
                                options = el.selectedOptions;
                                for (o in options) {
                                    option = options[o];
                                    if (typeof option.text !== 'undefined') {
                                        form[id].push({ text: option.text, value: option.value });
                                    }
                                }
                            } else {
                                idx = el.selectedIndex;
                                if (idx !== -1) {
                                    form[id].text = el[idx].text;
                                    form[id].value = el[idx].value;
                                    form[id].selectedIndex = idx;
                                }
                            }

                            break;
                    }
                }
            }

            return form;
        }
    }
});
