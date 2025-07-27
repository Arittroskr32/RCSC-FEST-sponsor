// Generic entity management JavaScript
// This file is used by partners.html, vendors.html, and participants.html

let currentEntities = [];

document.addEventListener('DOMContentLoaded', function() {
    loadEntityCount();
    
    // Add form submission handler
    document.getElementById('addEntityForm').addEventListener('submit', function(e) {
        e.preventDefault();
        addEntity();
    });
    
    // Add search on Enter key
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchEntities();
        }
    });
});

async function loadEntityCount() {
    try {
        const response = await fetch(`/api/${ENTITY_TYPE}/count`);
        const data = await response.json();
        document.getElementById('entity-count').textContent = data.count || 0;
    } catch (error) {
        console.error(`Error loading ${ENTITY_TYPE} count:`, error);
    }
}

async function searchEntities() {
    const searchTerm = document.getElementById('searchInput').value.trim();
    
    if (!searchTerm) {
        showAlert('Please enter a search term', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/${ENTITY_TYPE}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ search_term: searchTerm })
        });
        
        const entities = await response.json();
        displaySearchResults(entities);
    } catch (error) {
        console.error(`Error searching ${ENTITY_TYPE}:`, error);
        showAlert(`Error searching ${ENTITY_TYPE}`, 'error');
    }
}

function displaySearchResults(entities) {
    const resultsDiv = document.getElementById('searchResults');
    
    if (entities.length === 0) {
        resultsDiv.innerHTML = `<p class="no-results">No ${ENTITY_TYPE} found matching your search.</p>`;
        return;
    }
    
    let html = '<h4>Search Results:</h4><div class="results-grid">';
    
    entities.forEach(entity => {
        html += createEntityCard(entity);
    });
    
    html += '</div>';
    resultsDiv.innerHTML = html;
}

async function addEntity() {
    const form = document.getElementById('addEntityForm');
    const formData = new FormData(form);
    
    const entityData = {};
    for (let [key, value] of formData.entries()) {
        if (value) {
            if (key.includes('fee') || key.includes('amount') || key.includes('cost')) {
                entityData[key] = parseFloat(value);
            } else {
                entityData[key] = value;
            }
        }
    }
    
    try {
        const response = await fetch(`/api/${ENTITY_TYPE}/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(entityData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert(`${ENTITY_NAME} added successfully!`, 'success');
            form.reset();
            loadEntityCount();
        } else {
            showAlert(result.message || `Error adding ${ENTITY_NAME.toLowerCase()}`, 'error');
        }
    } catch (error) {
        console.error(`Error adding ${ENTITY_NAME.toLowerCase()}:`, error);
        showAlert(`Error adding ${ENTITY_NAME.toLowerCase()}`, 'error');
    }
}

async function loadAllEntities() {
    try {
        const response = await fetch(`/api/${ENTITY_TYPE}/list`);
        const entities = await response.json();
        
        currentEntities = entities;
        displayEntitiesList(entities);
    } catch (error) {
        console.error(`Error loading ${ENTITY_TYPE}:`, error);
        showAlert(`Error loading ${ENTITY_TYPE}`, 'error');
    }
}

function displayEntitiesList(entities) {
    const listDiv = document.getElementById('entitiesList');
    
    if (entities.length === 0) {
        listDiv.innerHTML = `<p class="no-results">No ${ENTITY_TYPE} found.</p>`;
        return;
    }
    
    let html = `<h4>All ${ENTITY_NAME}s:</h4><div class="results-grid">`;
    
    entities.forEach(entity => {
        html += createEntityCard(entity, true);
    });
    
    html += '</div>';
    listDiv.innerHTML = html;
}

function createEntityCard(entity, showCreatedBy = false) {
    let html = `
        <div class="result-card">
            <h5>${entity.name}</h5>
            <p><i class="fas fa-envelope"></i> ${entity.email}</p>
    `;
    
    // Add entity-specific fields
    if (entity.company) {
        html += `<p><i class="fas fa-building"></i> ${entity.company}</p>`;
    }
    if (entity.organization) {
        html += `<p><i class="fas fa-university"></i> ${entity.organization}</p>`;
    }
    if (entity.phone) {
        html += `<p><i class="fas fa-phone"></i> ${entity.phone}</p>`;
    }
    
    // Type-specific fields
    if (entity.partnership_type) {
        html += `<p><i class="fas fa-handshake"></i> ${entity.partnership_type}</p>`;
    }
    if (entity.service_type) {
        html += `<p><i class="fas fa-cogs"></i> ${entity.service_type}</p>`;
    }
    if (entity.participant_type) {
        html += `<p><i class="fas fa-user-tag"></i> ${entity.participant_type}</p>`;
    }
    
    // Financial fields
    if (entity.cost_estimate) {
        html += `<p><i class="fas fa-dollar-sign"></i> Cost: $${entity.cost_estimate}</p>`;
    }
    if (entity.registration_fee) {
        html += `<p><i class="fas fa-dollar-sign"></i> Fee: $${entity.registration_fee}</p>`;
    }
    
    html += `<p><i class="fas fa-calendar"></i> Added: ${entity.created_at}</p>`;
    
    if (showCreatedBy && entity.created_by) {
        html += `<p><i class="fas fa-user"></i> By: ${entity.created_by}</p>`;
    }
    
    html += `
            <button onclick="deleteEntity('${entity._id}')" class="btn btn-danger btn-sm">
                <i class="fas fa-trash"></i> Delete
            </button>
        </div>
    `;
    
    return html;
}

async function deleteEntity(entityId) {
    if (!confirm(`Are you sure you want to delete this ${ENTITY_NAME.toLowerCase()}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/${ENTITY_TYPE}/delete/${entityId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert(`${ENTITY_NAME} deleted successfully!`, 'success');
            loadEntityCount();
            // Refresh current view
            if (currentEntities.length > 0) {
                loadAllEntities();
            }
        } else {
            showAlert(result.message || `Error deleting ${ENTITY_NAME.toLowerCase()}`, 'error');
        }
    } catch (error) {
        console.error(`Error deleting ${ENTITY_NAME.toLowerCase()}:`, error);
        showAlert(`Error deleting ${ENTITY_NAME.toLowerCase()}`, 'error');
    }
}

function clearSearch() {
    document.getElementById('searchInput').value = '';
    document.getElementById('searchResults').innerHTML = '';
}
