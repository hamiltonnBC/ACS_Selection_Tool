document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('data_selection_form');
    const confirmation = document.getElementById('confirmation');
    const apiUrlDisplay = document.getElementById('api_url_display');
    const confirmYes = document.getElementById('confirm_yes');
    const confirmNo = document.getElementById('confirm_no');
    const year_select = document.getElementById('year_select');
    const data_option = document.getElementById('data_option');
    const variable_selection = document.getElementById('variable_selection');

    // Populate year options
    for (let year = 2022; year >= 2009; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        year_select.appendChild(option);
    }

    // Show/hide variable selection based on data option
    data_option.addEventListener('change', function() {
        variable_selection.style.display = 
            this.value === 'select_variables' ? 'block' : 'none';
    });

   // Form submission handler
   form.addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const data = Object.fromEntries(formData);

    // If 'entire_table' is selected, remove the selected_variables field
    if (data.data_option === 'entire_table') {
        delete data.selected_variables;
    }

    fetch('/api/generate_url', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(result => {
        if (result.api_url) {
            apiUrlDisplay.textContent = result.api_url;
            form.style.display = 'none';
            confirmation.style.display = 'block';
        } else {
            console.error('Error:', result.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});


if (confirmYes) {
    confirmYes.addEventListener('click', function() {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        data.api_url = apiUrlDisplay.textContent;

        fetch('/process_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => response.text())
        .then(html => {
            document.open();
            document.write(html);
            document.close();
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
}

    if (confirmNo) {
        confirmNo.addEventListener('click', function() {
            form.style.display = 'block';
            confirmation.style.display = 'none';
        });
    }
});
