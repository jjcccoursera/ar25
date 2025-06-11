
if (document.getElementById('coligs').classList.contains('visible-table')) {
    document.getElementById('distrito').value = 'Total nacional'
}


document.getElementById('coligs-btn').addEventListener('click', () => {
    window.location.reload(true);
    if (document.getElementById('coligs').classList.contains('hidden')) {
        // document.getElementById('coligs').classList.remove('hidden');
        // document.getElementById('coligs').classList.add ('visible-table');
        console.log(document.getElementById('coligs'));
        document.getElementById('resultados-btn').classList.remove('hidden');
        document.getElementById('resultados-btn').classList.add('inline-block');
        document.getElementById('resultados').classList.add('hidden');
        document.getElementById('resultados').classList.remove('visible-block');
        document.getElementById('resultados-btn').classList.add('hidden');
        document.getElementById('resultados-btn').classList.remove('inline-block');
    } else {
        if (document.getElementById('distrito').value === 'Total nacional') {
            document.getElementById('resultados').classList.remove('hidden');
            document.getElementById('resultados').classList.add('visible-block');
        } else {
            document.getElementById('distrito-div').classList.remove('hidden');
            document.getElementById('distrito-div').classList.add('visible-block');
        }
        document.getElementById('coligs').classList.add('hidden');
        document.getElementById('coligs').classList.remove = 'visible-table';
        document.getElementById('resultados-btn').classList.add('hidden');
        document.getElementById('resultados-btn').classList.remove('inline-block');   
    }
});


document.getElementById('resultados-btn').addEventListener('click', () => {
    const inputs = document.querySelectorAll('.group-input');
    const partidos_novo = {};
    
    inputs.forEach(input => {
        const label = input.dataset.label;
        const groups = input.value.split(',').map(s => s.trim());
        partidos_novo[label] = groups;
    });
    partidos_novo['Votos em branco'] = ['Votos em branco'];
    partidos_novo['Votos nulos'] = ['Votos nulos'];
    partidos = partidos_novo;

    // Send updated data to the server (example: console.log for now)
    // console.log(compareSorted(partidos, partidos_novo));
    document.getElementById('distrito-div').classList.remove('hidden');
    document.getElementById('distrito-div').classList.add('visible-block');
    document.getElementById('resultados-btn').classList.add('hidden');
    document.getElementById('resultados-btn').classList.remove('inline-block');  
    document.getElementById('coligs').classList.add('hidden');
    document.getElementById('coligs').classList.remove('visible-table');
    // if (compareSorted(partidos, partidos_novo)) {
    if (true) {
        const paroucolig = document.querySelector('input[name="paroucolig"]:checked').value;
        console.log(paroucolig);
        if (document.getElementById('distrito').value === 'Total nacional') {
            if (paroucolig === 'Partidos') {
                document.getElementById('resultados').classList.remove('hidden');
                document.getElementById('resultados').classList.add ('visible-block');
                document.getElementById('rescolig').classList.add('hidden');
                document.getElementById('rescolig').classList.remove ('visible-block');
            } else {
                document.getElementById('resultados').classList.add('hidden');
                document.getElementById('resultados').classList.remove ('visible-block');
                document.getElementById('rescolig').classList.remove('hidden');
                document.getElementById('rescolig').classList.add ('visible-block');
            }
        } else {
            document.getElementById('resultados').classList.add('hidden');
            document.getElementById('resultados').classList.remove('visible-block');
            document.getElementById('district-results-container').classList.remove('hidden');
            document.getElementById('district-results-container').classList.add('visible-block');
        }   
    } else {
        alert('Changes logged to console. Add your save logic here!');
    }
});

function compareSorted(a, b) {
    const sortedA = Object.entries(a).sort();
    const sortedB = Object.entries(b).sort();
    return JSON.stringify(sortedA) === JSON.stringify(sortedB);
}

document.getElementById('distrito').addEventListener('change', function() {
    const selectedDistrict = this.value;
    const nacionalDiv = document.getElementById('resultados');
    const districtDiv = document.getElementById('district-results-container');
    const resultsBut = document.getElementById('resultados-btn');
    const coligsDiv = document.getElementById('coligs');
    const rescoligDiv = document.getElementById('rescolig');
    const districtGroupDiv = document.getElementById('district-group-results-container');

    // Show national results and controls
    coligsDiv.classList.remove('visible-table');
    coligsDiv.classList.add('hidden');
   
    resultsBut.classList.remove('inline-block');
    resultsBut.classList.add('hidden');
    
    if (selectedDistrict === 'Total nacional') {

        districtDiv.classList.add('hidden');
        districtDiv.classList.remove('visible-block');
        
        if (document.getElementsByName('paroucolig')[0].checked) {
            nacionalDiv.classList.remove('hidden');
            nacionalDiv.classList.add('visible-block');
            rescoligDiv.classList.add('hidden');
            rescoligDiv.classList.remove('visible-block');
            districtGroupDiv.classList.add('hidden');
            districtGroupDiv.classList.remove('visible-block');
        } else {
            rescoligDiv.classList.remove('hidden');
            rescoligDiv.classList.add('visible-block'); 
            nacionalDiv.classList.add('hidden');
            nacionalDiv.classList.remove('visible-block');
            districtGroupDiv.classList.add('hidden');
            districtGroupDiv.classList.remove('visible-block');
        }  
    } else {
        nacionalDiv.classList.add('hidden');
        nacionalDiv.classList.remove('visible-block');
        rescoligDiv.classList.add('hidden');
        rescoligDiv.classList.remove('visible-block');
        
        document.getElementById('distrito').textContent = selectedDistrict;
        
        if (document.getElementsByName('paroucolig')[0].checked) {
            const districtData = getDistrictData(selectedDistrict);
            updateDistrictTable(districtData);
            districtDiv.classList.remove('hidden');
            districtDiv.classList.add('visible-block');
        } else {
            const districtGroupData = getDistrictGroupData(selectedDistrict);
            updateDistrictGroupTable(districtGroupData);
            districtGroupDiv.classList.remove('hidden');
            districtGroupDiv.classList.add('visible-block');
        }   
    }
});

function getDistrictData(selectedDistrict) {
    // Process and display district data by party
    // Get the raw encoded data
    const rawData = document.getElementById('election-data').getAttribute('data-districts');

    // Decode HTML entities first
    const decodedData = new DOMParser()
    .parseFromString(rawData, 'text/html')
    .documentElement.textContent;

    // Then parse JSON
    const electionData = JSON.parse(decodedData);
    return districtData = getElectionData()[selectedDistrict] || {};
}


function updateDistrictTable(data) {
    const table = document.getElementById('district-table');
    const tbody = table.querySelector('tbody');
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    // Calculate totals
    const totalVotes = Object.values(data).reduce((sum, p) => sum + (p.votos || 0), 0);
    const totalMandates = Object.values(data).reduce((sum, p) => sum + (p.mandatos || 0), 0);
    
    // Filter out special entries and sort
    const parties = Object.entries(data)
        .filter(([party]) => !['TOTAL', 'Votos em branco', 'Votos nulos'].includes(party))
        .sort((a, b) => b[1].votos - a[1].votos);
    
    // Add party rows
    parties.forEach(([party, {votos, mandatos}]) => {
        const votesPerMandate = mandatos > 0 ? Math.round(votos/mandatos) : null;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="padding: 4px;">${party}</td>
            <td style="padding: 4px; text-align: right;">${votos.toLocaleString('pt-PT')}</td>
            <td style="padding: 4px; text-align: right;">${((votos/(totalVotes - (data['Votos em branco']?.votos || 0) - (data['Votos nulos']?.votos || 0)))*100).toFixed(2)}%</td>
            <td style="padding: 4px; text-align: right;">${mandatos > 0 ? mandatos : ''}</td>
            <td style="padding: 4px; text-align: right;">${votesPerMandate ? votesPerMandate.toLocaleString('pt-PT') : ''}</td>
        `;
        tbody.appendChild(row);
    });
    
    // Add "Votos válidos" subtotal row
    const validRow = document.createElement('tr');
    validRow.style.cssText = 'font-weight: bold; background-color: #e6f7e6; border-top: 2px solid #dbcfcf;';
    validRow.innerHTML = `
        <td style="padding: 8px;">Votos válidos</td>
        <td style="padding: 8px; text-align: right;">${(totalVotes - (data['Votos em branco']?.votos || 0) - (data['Votos nulos']?.votos || 0)).toLocaleString('pt-PT')}</td>
        <td style="padding: 8px; text-align: right;">100.00%</td>
        <td style="padding: 8px; text-align: right;">${totalMandates.toLocaleString('pt-PT')}</td>
        <td style="padding: 8px; text-align: right;"> ${totalMandates > 0 ? Math.round(totalVotes/totalMandates).toLocaleString('pt-PT') : ''}</td>
    `;
    tbody.appendChild(validRow);
    
    // Add blank votes if they exist
    if (data['Votos em branco']) {
        const blankRow = document.createElement('tr');
        blankRow.style.cssText = 'background-color: white;';
        blankRow.innerHTML = `
            <td style="padding: 8px;">Votos em branco</td>
            <td style="padding: 8px; text-align: right;">${data['Votos em branco'].votos.toLocaleString('pt-PT')}</td>
            <td style="padding: 8px; text-align: right;">${(data['Votos em branco'].votos/(totalVotes + data['Votos em branco'].votos + (data['Votos nulos']?.votos || 0)*100)).toFixed(2)}%</td>
            <td colspan="2"></td>
        `;
        tbody.appendChild(blankRow);
    }
    
    // Add null votes if they exist
    if (data['Votos nulos']) {
        const nullRow = document.createElement('tr');
        nullRow.style.cssText = 'background-color: white;';
        nullRow.innerHTML = `
            <td style="padding: 8px;">Votos nulos</td>
            <td style="padding: 8px; text-align: right;">${data['Votos nulos'].votos.toLocaleString('pt-PT')}</td>
            <td style="padding: 8px; text-align: right;">${(data['Votos nulos'].votos/(totalVotes + (data['Votos em branco']?.votos || 0) + data['Votos nulos'].votos)*100).toFixed(2)}%</td>
            <td colspan="2"></td>
        `;
        tbody.appendChild(nullRow);
    }
    
    // Add grand total row
    const totalAll = totalVotes;
    const totalRow = document.createElement('tr');
    totalRow.style.cssText = 'font-weight: bold; background-color: #e6f7e6; border-top: 2px solid #000;';
    totalRow.innerHTML = `
        <td style="padding: 8px;">TOTAL</td>
        <td style="padding: 8px; text-align: right;">${totalAll.toLocaleString('pt-PT')}</td>
        <td style="padding: 8px; text-align: right;">100.00%</td>
        <td colspan="2"></td>
    `;
    tbody.appendChild(totalRow);
    
    // Make table visible
    table.classList.remove('hidden');
}

function getElectionData() {
    try {
      const container = document.getElementById('election-data');
      if (!container) throw new Error('Data container not found');
      
      const raw = container.getAttribute('data-districts');
      if (!raw) throw new Error('No data attribute found');
      
      const decoded = new DOMParser().parseFromString(raw, 'text/html').documentElement.textContent;
      return JSON.parse(decoded);
    } catch (error) {
      console.error('Failed to load election data:', error);
      return {}; // Return empty object as fallback
    }
}

function updateDistrictGroupTable(data) {
    const table = document.getElementById('district-group-table');
    const tbody = table.querySelector('tbody');
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    // Calculate totals
    const totalVotes = Object.values(data).reduce((sum, p) => sum + (p.votos || 0), 0);
    const totalMandates = Object.values(data).reduce((sum, p) => sum + (p.mandatos || 0), 0);
    
    // Filter out special entries and sort
    const groups = Object.entries(data)
        .filter(([group]) => !['TOTAL', 'Votos em branco', 'Votos nulos'].includes(group))
        .sort((a, b) => b[1].votos - a[1].votos);
    
    // Add party rows
    groups.forEach(([group, {votos, mandatos}]) => {
        const votesPerMandate = mandatos > 0 ? Math.round(votos/mandatos) : null;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="padding: 4px;">${group}</td>
            <td style="padding: 4px; text-align: right;">${votos.toLocaleString('pt-PT')}</td>
            <td style="padding: 4px; text-align: right;">${((votos/(totalVotes - (data['Votos em branco']?.votos || 0) - (data['Votos nulos']?.votos || 0)))*100).toFixed(2)}%</td>
            <td style="padding: 4px; text-align: right;">${mandatos > 0 ? mandatos : ''}</td>
            <td style="padding: 4px; text-align: right;">${votesPerMandate ? votesPerMandate.toLocaleString('pt-PT') : ''}</td>
        `;
        tbody.appendChild(row);
    });
    
    // Add "Votos válidos" subtotal row
    const validRow = document.createElement('tr');
    validRow.style.cssText = 'font-weight: bold; background-color: #e6f7e6; border-top: 2px solid #dbcfcf;';
    validRow.innerHTML = `
        <td style="padding: 8px;">Votos válidos</td>
        <td style="padding: 8px; text-align: right;">${(totalVotes - (data['Votos em branco']?.votos || 0) - (data['Votos nulos']?.votos || 0)).toLocaleString('pt-PT')}</td>
        <td style="padding: 8px; text-align: right;">100.00%</td>
        <td style="padding: 8px; text-align: right;">${totalMandates.toLocaleString('pt-PT')}</td>
        <td style="padding: 8px; text-align: right;"> ${totalMandates > 0 ? Math.round(totalVotes/totalMandates).toLocaleString('pt-PT') : ''}</td>
    `;
    tbody.appendChild(validRow);
    
    // Add blank votes if they exist
    if (data['Votos em branco']) {
        const blankRow = document.createElement('tr');
        blankRow.style.cssText = 'background-color: white;';
        blankRow.innerHTML = `
            <td style="padding: 8px;">Votos em branco</td>
            <td style="padding: 8px; text-align: right;">${data['Votos em branco'].votos.toLocaleString('pt-PT')}</td>
            <td style="padding: 8px; text-align: right;">${(data['Votos em branco'].votos/(totalVotes + data['Votos em branco'].votos+ (data['Votos nulos']?.votos || 0)*100)).toFixed(2)}%</td>
            <td colspan="2"></td>
        `;
        tbody.appendChild(blankRow);
    }
    
    // Add null votes if they exist
    if (data['Votos nulos']) {
        const nullRow = document.createElement('tr');
        nullRow.style.cssText = 'background-color: white;';
        nullRow.innerHTML = `
            <td style="padding: 8px;">Votos nulos</td>
            <td style="padding: 8px; text-align: right;">${data['Votos nulos'].votos.toLocaleString('pt-PT')}</td>
            <td style="padding: 8px; text-align: right;">${(data['Votos nulos'].votos/(totalVotes + (data['Votos em branco']?.votos || 0) + data['Votos nulos'].votos)*100).toFixed(2)}%</td>
            <td colspan="2"></td>
        `;
        tbody.appendChild(nullRow);
    }
    
    // Add grand total row
    const totalAll = totalVotes;
    const totalRow = document.createElement('tr');
    totalRow.style.cssText = 'font-weight: bold; background-color: #e6f7e6; border-top: 2px solid #000;';
    totalRow.innerHTML = `
        <td style="padding: 8px;">TOTAL</td>
        <td style="padding: 8px; text-align: right;">${totalAll.toLocaleString('pt-PT')}</td>
        <td style="padding: 8px; text-align: right;">100.00%</td>
        <td colspan="2"></td>
    `;
    tbody.appendChild(totalRow);
    
    // Make table visible
    table.classList.remove('hidden');
}

function getDistrictGroupData(selectedDistrict) {
    // Get the raw encoded data for GROUPS
    const rawGroupData = document.getElementById('election-group-data').getAttribute('data-district-groups');
    
    // Decode HTML entities and parse JSON
    const decodedGroupData = new DOMParser()
        .parseFromString(rawGroupData, 'text/html')
        .documentElement.textContent;
    
    const electionGroupData = JSON.parse(decodedGroupData);
    return electionGroupData[selectedDistrict] || {};
}

  document.addEventListener('DOMContentLoaded', function() {
    // Get all radio buttons with name="paroucolig"
    const radioButtons = document.querySelectorAll('input[name="paroucolig"]');
    
    // Add change event listener to each radio button
    radioButtons.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.checked) {
                // Execute different code based on selected value
                const selectedDistrict = document.getElementById('distrito').value;
                console.log(selectedDistrict);
                if (this.value === 'Partidos') {
                    console.log('Partidos selected');
                    // Your code for "Partidos" selection here
                    if (document.getElementById('distrito').value === 'Total nacional') {
                        document.getElementById('resultados').classList.remove('hidden');
                        document.getElementById('resultados').classList.add('visible-block');
                        document.getElementById('rescolig').classList.add('hidden');
                        document.getElementById('rescolig').classList.remove ('visible-block');
                        document.getElementById('district-results-container').classList.add('hidden');
                        document.getElementById('district-results-container').classList.remove('visible-block');
                        document.getElementById('district-group-results-container').classList.add('hidden');
                        document.getElementById('district-group-results-container').classList.remove('visible-block');
                    } else {
                        document.getElementById('district-results-container').classList.remove('hidden');
                        document.getElementById('district-results-container').classList.add('visible-block');
                        document.getElementById('resultados').classList.add('hidden');
                        document.getElementById('resultados').classList.remove ('visible-block');
                        document.getElementById('district-group-results-container').classList.add('hidden');
                        document.getElementById('district-group-results-container').classList.remove('visible-block');
                        document.getElementById('rescolig').classList.add('hidden');
                        document.getElementById('rescolig').classList.remove ('visible-block');
                        const districtData = getDistrictData(selectedDistrict);
                        updateDistrictTable(districtData);
                    }
                } else if (this.value === 'Coligações') {
                    console.log('Coligações selected');
                    // Your code for "Coligações" selection here
                    if (document.getElementById('distrito').value === 'Total nacional') {
                        document.getElementById('rescolig').classList.remove('hidden');
                        document.getElementById('rescolig').classList.add ('visible-block');
                        document.getElementById('resultados').classList.add('hidden');
                        document.getElementById('resultados').classList.remove ('visible-block');
                        document.getElementById('district-results-container').classList.add('hidden');
                        document.getElementById('district-results-container').classList.remove ('visible-block');
                        document.getElementById('district-group-results-container').classList.add('hidden');
                        document.getElementById('district-group-results-container').classList.remove('visible-block');
                    } else {
                        document.getElementById('district-group-results-container').classList.remove('hidden');
                        document.getElementById('district-group-results-container').classList.add('visible-block');
                        document.getElementById('district-results-container').classList.add('hidden');
                        document.getElementById('district-results-container').classList.remove ('visible-block');
                        document.getElementById('resultados').classList.add('hidden');
                        document.getElementById('resultados').classList.remove ('visible-block');
                        document.getElementById('rescolig').classList.add('hidden');
                        document.getElementById('rescolig').classList.remove ('visible-block');
                        const districtData = getDistrictGroupData(selectedDistrict);
                        updateDistrictGroupTable(districtData);
                    }
                }
            }
        });
    });
    
});
