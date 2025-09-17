document.addEventListener('DOMContentLoaded', () => {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('start_date').value = today;
    const oneWeekFromNow = new Date(new Date().setDate(new Date().getDate() + 7)).toISOString().split('T')[0];
    document.getElementById('end_date').value = oneWeekFromNow;
    addRoom();
});

function addRoom() {
    const roomContainer = document.getElementById('room-container');
    const roomIndex = roomContainer.children.length;

    const roomSection = document.createElement('div');
    roomSection.className = 'room-section';
    roomSection.innerHTML = `
        <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-bold">Room #${roomIndex + 1}</h3>
            <button onclick="removeRoom(this)" class="text-sm text-gray-500 hover:text-red-500">Remove Room</button>
        </div>
        <div class="flex flex-col mb-4">
            <label class="mb-1 text-sm font-medium text-gray-700">Room Name</label>
            <input type="text" class="w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g., TjÃ¸rnin">
        </div>
        <div class="staff-list">
            <div class="staff-member">
                <div class="flex flex-col">
                    <label class="mb-1 text-sm font-medium text-gray-700">Staff Initial</label>
                    <input type="text" class="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g., J">
                </div>
                <div class="flex flex-col">
                    <label class="mb-1 text-sm font-medium text-gray-700">Contracted Hours</label>
                    <input type="number" step="0.5" class="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g., 35">
                </div>
                <div class="flex flex-col">
                    <label class="mb-1 text-sm font-medium text-gray-700">Target Hours</label>
                    <input type="number" step="0.5" class="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g., 34.5">
                </div>
                <div class="flex flex-col">
                    <label class="mb-1 text-sm font-medium text-gray-700">Constraints</label>
                    <input type="text" class="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g., None">
                </div>
                <div class="flex items-center space-x-2">
                    <input type="checkbox" class="rounded text-blue-600 focus:ring-blue-500" id="open-room-${roomIndex}-0">
                    <label for="open-room-${roomIndex}-0" class="text-sm font-medium text-gray-700">Open Room</label>
                </div>
                <div class="flex items-center space-x-2">
                    <input type="checkbox" class="rounded text-blue-600 focus:ring-blue-500" id="closer-${roomIndex}-0">
                    <label for="closer-${roomIndex}-0" class="text-sm font-medium text-gray-700">Closer</label>
                </div>
            </div>
        </div>
        <button onclick="addStaff(this)" class="mt-4 text-sm text-blue-600 hover:underline">Add Staff Member</button>
    `;
    roomContainer.appendChild(roomSection);
}

function removeRoom(button) {
    button.closest('.room-section').remove();
}

function addStaff(button) {
    const roomSection = button.closest('.room-section');
    const roomIndex = Array.from(roomSection.parentNode.children).indexOf(roomSection);
    const staffList = roomSection.querySelector('.staff-list');
    const staffIndex = staffList.children.length;

    const staffMember = document.createElement('div');
    staffMember.className = 'staff-member';
    staffMember.innerHTML = `
        <div class="flex flex-col">
            <label class="mb-1 text-sm font-medium text-gray-700">Staff Initial</label>
            <input type="text" class="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g., J">
        </div>
        <div class="flex flex-col">
            <label class="mb-1 text-sm font-medium text-gray-700">Contracted Hours</label>
            <input type="number" step="0.5" class="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g., 35">
        </div>
        <div class="flex flex-col">
            <label class="mb-1 text-sm font-medium text-gray-700">Target Hours</label>
            <input type="number" step="0.5" class="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g., 34.5">
        </div>
        <div class="flex flex-col">
            <label class="mb-1 text-sm font-medium text-gray-700">Constraints</label>
            <input type="text" class="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="e.g., None">
        </div>
        <div class="flex items-center space-x-2">
            <input type="checkbox" class="rounded text-blue-600 focus:ring-blue-500" id="open-room-${roomIndex}-${staffIndex}">
            <label for="open-room-${roomIndex}-${staffIndex}" class="text-sm font-medium text-gray-700">Open Room</label>
        </div>
        <div class="flex items-center space-x-2">
            <input type="checkbox" class="rounded text-blue-600 focus:ring-blue-500" id="closer-${roomIndex}-${staffIndex}">
            <label for="closer-${roomIndex}-${staffIndex}" class="text-sm font-medium text-gray-700">Closer</label>
        </div>
    `;
    staffList.appendChild(staffMember);
}

function loadSampleData() {
    // Clear existing rooms
    const roomContainer = document.getElementById('room-container');
    roomContainer.innerHTML = '';

    // Certified staff
    document.getElementById('certified_staff').value = "J, H, B, M.B, K.Ã˜";

    // All 5 rooms data
    const allRoomsData = 
    [
{
    "name": "TjÃ¸rnin",
    "staff": [
        {
            "initial": "H",
            "contracted_hours_week": 35,
            "target_weekly_hours": 34.5,
            "constraints": "None",
            "open_room":"True",
            "closer":"False"

        },
        {
            "initial": "J",
            "contracted_hours_week": 35,
            "target_weekly_hours": 34.5,
            "constraints": "None",
            "open_room":"False",
            "closer":"False"
        }
    ]
},
{
    "name": "MÃ½ran",
    "staff": [
        {
            "initial": "M.B",
            "contracted_hours_week": 35,
            "target_weekly_hours": 34.5,
            "constraints": "None",
            "open_room":"True",
            "closer":"False"                    
        },
        {
            "initial": "M",
            "contracted_hours_week": 35,
            "target_weekly_hours": 34.5,
            "constraints": "None",
            "open_room":"False",
            "closer":"True"                    
        },
        {
            "initial": "K.Ã˜",
            "contracted_hours_week": 30,
            "target_weekly_hours": 29.5,
            "constraints": "None",
            "open_room":"False",
            "closer":"False"                    
        },
        {
            "initial": "J",
            "contracted_hours_week": 30,
            "target_weekly_hours": 29.5,
            "constraints": "Hard Constraint: Works a fixed shift of 09:00 - 15:00 every day.",
            "open_room":"False",
            "closer":"True"                   
        }
    ]
},
{
    "name": "TÃºgvan",
    "staff": [
        {
            "initial": "M",
            "contracted_hours_week": 35,
            "target_weekly_hours": 34.5,
            "constraints": "None",
            "open_room":"True",
            "closer":"False"
        },
        {
            "initial": "B",
            "contracted_hours_week": 35,
            "target_weekly_hours": 34.5,
            "constraints": "None",
            "open_room":"False",
            "closer":"True"                    
        },
        {
            "initial": "A",
            "contracted_hours_week": 33,
            "target_weekly_hours": 32.5,
            "constraints": "None",
            "open_room":"False",
            "closer":"False"
        }
    ]
},
{
    "name": "LÃ¸kurin",
    "staff": [
        {
            "initial": "S",
            "contracted_hours_week": 35,
            "target_weekly_hours": 34.5,
            "constraints": "None",
            "open_room":"False",
            "closer":"False"
        },
        {
            "initial": "M",
            "contracted_hours_week": 30,
            "target_weekly_hours": 29.5,
            "constraints": "None",
            "open_room":"False",
            "closer":"False"                    
        },
        {
            "initial": "N",
            "contracted_hours_week": 32,
            "target_weekly_hours": 31.5,
            "constraints": "Hard Constraint: Works only Monday to Thursday, from 08:00 to 16:00.",
            "open_room":"False",
            "closer":"False"
        }
    ]
},
{
    "name": "SpÃ­rar",
    "staff": [
        {
            "initial": "H",
            "contracted_hours_week": 30,
            "target_weekly_hours": 29.5,
            "constraints": "None",
            "open_room":"False",
            "closer":"False"
        },
        {
            "initial": "J",
            "contracted_hours_week": 35,
            "target_weekly_hours": 34.5,
            "constraints": "None",
            "open_room":"False",
            "closer":"False"
        },
        {
            "initial": "B",
            "contracted_hours_week": 35,
            "target_weekly_hours": 34.5,
            "constraints": "None",
            "open_room":"False",
            "closer":"False"
        },
        {
            "initial": "Starv",
            "contracted_hours_week": 35,
            "target_weekly_hours": 34.5,
            "constraints": "Note: This is a vacant position. Treat as a regular staff member for now.",
            "open_room":"False",
            "closer":"False"
        }
    ]
}
];

    allRoomsData.forEach(roomData => addRoomWithData(roomData));
}

function addRoomWithData(data) {
    const roomContainer = document.getElementById('room-container');
    const roomIndex = roomContainer.children.length;

    const roomSection = document.createElement('div');
    roomSection.className = 'room-section';
    roomSection.innerHTML = `
        <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-bold">Room #${roomIndex + 1}</h3>
            <button onclick="removeRoom(this)" class="text-sm text-gray-500 hover:text-red-500">Remove Room</button>
        </div>
        <div class="flex flex-col mb-4">
            <label class="mb-1 text-sm font-medium text-gray-700">Room Name</label>
            <input type="text" class="w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" value="${data.name}">
        </div>
        <div class="staff-list"></div>
        <button onclick="addStaff(this)" class="mt-4 text-sm text-blue-600 hover:underline">Add Staff Member</button>
    `;
    roomContainer.appendChild(roomSection);

    const staffList = roomSection.querySelector('.staff-list');
    data.staff.forEach((staffData, staffIndex) => {
        const staffMember = document.createElement('div');
        staffMember.className = 'staff-member';
        staffMember.innerHTML = `
            <div class="flex flex-col">
                <label class="mb-1 text-sm font-medium text-gray-700">Staff Initial</label>
                <input type="text" class="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" value="${staffData.initial}">
            </div>
            <div class="flex flex-col">
                <label class="mb-1 text-sm font-medium text-gray-700">Contracted Hours</label>
                <input type="number" step="0.5" class="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" value="${staffData.contracted_hours_week}">
            </div>
            <div class="flex flex-col">
                <label class="mb-1 text-sm font-medium text-gray-700">Target Hours</label>
                <input type="number" step="0.5" class="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" value="${staffData.target_weekly_hours}">
            </div>
            <div class="flex flex-col">
                <label class="mb-1 text-sm font-medium text-gray-700">Constraints</label>
                <input type="text" class="px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" value="${staffData.constraints}">
            </div>
            <div class="flex items-center space-x-2">
                <input type="checkbox" class="rounded text-blue-600 focus:ring-blue-500" id="open-room-${roomIndex}-${staffIndex}" ${staffData.open_room ? 'checked' : ''}>
                <label for="open-room-${roomIndex}-${staffIndex}" class="text-sm font-medium text-gray-700">Open Room</label>
            </div>
            <div class="flex items-center space-x-2">
                <input type="checkbox" class="rounded text-blue-600 focus:ring-blue-500" id="closer-${roomIndex}-${staffIndex}" ${staffData.closer ? 'checked' : ''}>
                <label for="closer-${roomIndex}-${staffIndex}" class="text-sm font-medium text-gray-700">Closer</label>
            </div>
        `;
        staffList.appendChild(staffMember);
    });
}


async function generateSchedule() {
    const spinner = document.getElementById('spinner');
    const buttonText = document.getElementById('button-text');
    const errorMessageDiv = document.getElementById('error-message');
    const statusMessageDiv = document.getElementById('status-message');
    const scheduleOutputDiv = document.getElementById('schedule-output');

    spinner.classList.remove('hidden');
    buttonText.textContent = 'Generating...';
    errorMessageDiv.classList.add('hidden');
    statusMessageDiv.classList.add('hidden');
    scheduleOutputDiv.innerHTML = '';

    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    const certifiedStaff = document.getElementById('certified_staff').value.split(',').map(s => s.trim()).filter(s => s);

    const rooms = [];
    const roomSections = document.querySelectorAll('#room-container > .room-section');
    roomSections.forEach(roomSection => {
        const roomName = roomSection.querySelector('input').value;
        const staff = [];
        const staffMembers = roomSection.querySelectorAll('.staff-member');
        staffMembers.forEach(staffMember => {
            const inputs = staffMember.querySelectorAll('input');
            const checkboxes = staffMember.querySelectorAll('input[type="checkbox"]');
            staff.push({
                initial: inputs[0].value,
                contracted_hours_week: parseFloat(inputs[1].value),
                target_weekly_hours: parseFloat(inputs[2].value),
                constraints: inputs[3].value,
                open_room: checkboxes[0].checked,
                closer: checkboxes[1].checked
            });
        });
        rooms.push({ name: roomName, staff: staff });
    });

    const data = {
        start_date: startDate,
        end_date: endDate,
        certified_staff: certifiedStaff,
        rooms: rooms
    };

    console.log("Sending JSON:", JSON.stringify(data, null, 2));

    try {
        const response = await fetch('http://127.0.0.1:8000/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to generate schedule.');
        }

        const result = await response.json();
        console.log("Received data:", result);
        
        // --- Schedule Display Logic (Updated Section) ---
        const schedule = result.updated_schedule;
        const violations = result.new_violations || [];
        const discrepancies = result.new_discrepancies || [];

        
        if (schedule && schedule.schedules) {
            const timeBlocks = ["07:30-08:00", "08:00-08:30", "08:30-09:00", "09:00-11:30", "11:30-13:00", "13:00-14:00", "14:00-16:00", "16:00-16:30", "16:30-17:00" ];
            const daysOfWeek = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
            
            schedule.schedules.forEach(roomSchedule => {
                const roomName = roomSchedule.room;
                for (const week in roomSchedule.weeks) {
                    const dailySchedule = roomSchedule.weeks[week];
                    
                    let tableHTML = `
                        <div class="my-8">
                            <h3 class="text-2xl font-bold mb-2">Room: ${roomName} (${week.charAt(0).toUpperCase() + week.slice(1)})</h3>
                            <table class="min-w-full divide-y divide-gray-200 shadow-lg rounded-lg overflow-hidden">
                                <thead class="bg-gray-100">
                                    <tr>
                                        <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time Block</th>
                                        ${daysOfWeek.map(day => `<th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">${day.charAt(0).toUpperCase() + day.slice(1)}</th>`).join('')}
                                    </tr>
                                </thead>
                                <tbody class="bg-white divide-y divide-gray-200">
                    `;

                    timeBlocks.forEach(block => {
            tableHTML += `<tr data-time-block="${block}">
                <td class="py-2 px-4 border font-medium">${block}</td>`;
            daysOfWeek.forEach(day => {
                const staffArr = dailySchedule[day]?.[block];
                const staff = Array.isArray(staffArr) ? staffArr.join(', ') : '';
                tableHTML += `<td 
                    class="py-2 px-4 border editable-cell" 
                    data-day="${day}"
                    data-room-name="${roomName}"
                    contenteditable="true"
                    onblur="handleScheduleEdit(event)">${staff}</td>`;
            });
            tableHTML += `</tr>`;
        });

        // Add Friday Early Leave row at the bottom
        tableHTML += `<tr>
            <td class="py-2 px-4 border font-bold">Friday Early Leave</td>
            <td 
                class="py-2 px-4 border editable-cell"
                colspan="${daysOfWeek.length}"
                contenteditable="true"
                data-friday-early-leave="true"
                data-room-name="${roomName}"
                data-week="${week}"
                onblur="handleScheduleEdit(event)"
            >${dailySchedule.fridayEarlyLeave || ""}</td>
        </tr>`;

        tableHTML += `</tbody></table></div>`;

                    tableHTML += `</tbody></table></div>`;
                    scheduleOutputDiv.innerHTML += tableHTML;
                }
            });

            // Call the correct display functions
            displayDiscrepancies(discrepancies);
            renderViolations(violations);

        } else {
            statusMessageDiv.textContent = 'No schedule data returned.';
            statusMessageDiv.classList.remove('hidden');
        }

    } catch (error) {
        console.error('Error generating schedule:', error);
        errorMessageDiv.textContent = error.message;
        errorMessageDiv.classList.remove('hidden');
    } finally {
        spinner.classList.add('hidden');
        buttonText.textContent = 'Generate Schedule';
    }
}

// Function to get the full schedule data from the DOM table
// Fixed version of getScheduleFromDOM function
function getScheduleFromDOM() {
const timeBlocks = ["07:30-08:00", "08:00-08:30", "08:30-09:00", "09:00-11:30", "11:30-13:00", "13:00-14:00", "14:00-16:00", "16:00-16:30", "16:30-17:00"];
const daysOfWeek = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
const schedules = [];

// Get all room divs in the schedule output
const roomDivs = document.querySelectorAll('#schedule-output > div');
console.log(`Found ${roomDivs.length} room divs`);

roomDivs.forEach((roomDiv, index) => {
const h3Element = roomDiv.querySelector('h3');
if (!h3Element) {
    console.warn(`No h3 element found in room div ${index}`);
    return;
}

const h3Text = h3Element.textContent;
console.log(`Processing room div: ${h3Text}`);

// Extract room name and week - handle both formats
const roomMatch = h3Text.match(/Room:\s*([^(]+)\s*\(/);
const weekMatch = h3Text.match(/\(([^)]+)\)/);

if (!roomMatch || !weekMatch) {
    console.warn(`Could not parse room/week from: ${h3Text}`);
    return;
}

const roomName = roomMatch[1].trim();
let weekName = weekMatch[1].toLowerCase().replace(/\s+/g, '');

// Normalize week name (Week1, Week 1, week1 -> week1)
if (weekName.startsWith('week')) {
    weekName = weekName;
} else {
    weekName = 'week1'; // fallback
}

console.log(`Room: ${roomName}, Week: ${weekName}`);

// Find existing schedule for this room or create new one
let roomSchedule = schedules.find(s => s.room === roomName);
if (!roomSchedule) {
    roomSchedule = {
        room: roomName,
        weeks: {}
    };
    schedules.push(roomSchedule);
}

// Initialize the week if it doesn't exist
if (!roomSchedule.weeks[weekName]) {
    roomSchedule.weeks[weekName] = {};
}

// Get the table rows
const table = roomDiv.querySelector('table');
if (!table) {
    console.warn(`No table found in room div for ${roomName}`);
    return;
}

const rows = table.querySelectorAll('tbody tr');
console.log(`Found ${rows.length} rows for ${roomName} ${weekName}`);

rows.forEach((row, rowIndex) => {
    const timeBlock = timeBlocks[rowIndex]; // Use index instead of dataset
    if (!timeBlock) {
        console.warn(`No time block for row ${rowIndex}`);
        return;
    }
    
    const cells = row.querySelectorAll('td.editable-cell');
    console.log(`Processing time block ${timeBlock} with ${cells.length} cells`);
    
    cells.forEach((cell, dayIndex) => {
        const day = daysOfWeek[dayIndex];
        if (!day) {
            console.warn(`No day for cell index ${dayIndex}`);
            return;
        }
        
        // Parse staff from cell content
        const cellText = cell.textContent.trim();
        const staff = cellText ? cellText.split(',').map(s => s.trim()).filter(s => s.length > 0) : [];
        
        // Ensure staff array is never empty (validation requires minItems: 1)
        if (staff.length === 0) {
            staff.push('STAFF_NEEDED'); // placeholder
        }
        
        // Initialize day if it doesn't exist
        if (!roomSchedule.weeks[weekName][day]) {
            roomSchedule.weeks[weekName][day] = {};
        }
        
        roomSchedule.weeks[weekName][day][timeBlock] = staff;
        console.log(`Set ${roomName} ${weekName} ${day} ${timeBlock}: ${staff.join(', ')}`);
    });
});

const fridayEarlyLeaveCell = table.querySelector('td[data-friday-early-leave="true"]');
if (fridayEarlyLeaveCell) {
    roomSchedule.weeks[weekName].fridayEarlyLeave = fridayEarlyLeaveCell.textContent.trim();
}

});

console.log('Final schedules structure:', JSON.stringify(schedules, null, 2));

return { updated_schedule: { schedules } };
}

// Function to handle schedule edits
// Function to handle schedule edits
async function handleScheduleEdit(event) {
const spinner = document.getElementById('spinner');
spinner.classList.remove('hidden');

const updatedSchedule = getScheduleFromDOM();

// Extract target hours from the form data
const target_hours = {};
const roomSections = document.querySelectorAll('#room-container > .room-section');
roomSections.forEach(roomSection => {
const staffMembers = roomSection.querySelectorAll('.staff-member');
staffMembers.forEach(staffMember => {
    const inputs = staffMember.querySelectorAll('input');
    const staffInitial = inputs[0].value.trim();
    const targetHours = parseFloat(inputs[2].value);
    if (staffInitial && !isNaN(targetHours)) {
        target_hours[staffInitial] = targetHours;
    }
});
});

try {
const response = await fetch('http://127.0.0.1:8000/validate/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        updated_schedule: updatedSchedule.updated_schedule,
        target_hours: target_hours
    }),
});

if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to update schedule and re-evaluate violations.');
}

const result = await response.json();
console.log("Re-evaluation result:", result);

// Check the structure of the response
if (result.violations) {
    // Re-render the violation and discrepancy sections
    renderViolations(result.violations);
} else {
    console.error('No violations data in response:', result);
}

if (result.discrepancies) {
    displayDiscrepancies(result.discrepancies);
} else {
    console.log('No discrepancies data in response');
}

} catch (error) {
console.error('Error updating schedule:', error);
const errorMessageDiv = document.getElementById('error-message');
errorMessageDiv.textContent = error.message;
errorMessageDiv.classList.remove('hidden');
} finally {
spinner.classList.add('hidden');
}
}


// Display new discrepancies in the corresponding container
function displayDiscrepancies(discrepancies) {
    const container = document.getElementById('new_discrepancies_container');
    container.innerHTML = ''; // Clear previous content
    if (!discrepancies || discrepancies.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center">No discrepancies found.</p>';
        return;
    }
    discrepancies.forEach(item => {
        const card = document.createElement('div');
        card.className = 'p-4 bg-white border border-gray-200 rounded-lg shadow mb-4';
        card.innerHTML = `
            <h3 class="font-bold text-lg text-gray-800 mb-2">${item.staff_id} - ${item.week}</h3>
            <p class="text-sm text-gray-600"><strong>Calculated Hours/Week:</strong> ${item.calculated_hours}</p>
            <p class="text-sm text-gray-600"><strong>Expected Hours Hours/Week:</strong> ${item.expected_hours}</p>
            <p class="text-sm text-gray-600"><strong>Difference:</strong> <span class="font-semibold ${item.difference < 0 ? 'text-red-500' : 'text-green-500'}">${item.difference}</span></p>
        `;
        container.appendChild(card);
    });
}

// Display new violations in the corresponding container
function renderViolations(violations) {
if (!violations || !violations.summary) {
    console.error('Invalid data structure received from backend.');
    return;
}

const violationsData = violations.violations;
const summaryData = violations.summary;

// Render Summary
const summaryContainer = document.getElementById('violations_summary_container');
summaryContainer.innerHTML = `
    <p class="text-lg"><strong>Total Violations:</strong> <span class="text-red-600">${summaryData.total_violations}</span></p>
    <div class="bg-gray-100 p-4 rounded-lg">
        <p class="font-semibold text-gray-700">Violations by Constraint:</p>
        <ul class="list-disc list-inside text-sm text-gray-600">
            <li>Weekly Hours: ${summaryData.violations_by_constraint.constraint_3_weekly_hours}</li>
            <li>Friday Early Leave: ${summaryData.violations_by_constraint.constraint_4_friday_early_leave}</li>
            <li>Fixed Schedules: ${summaryData.violations_by_constraint.constraint_5_fixed_schedules}</li>
            <li>Staffing Levels: ${summaryData.violations_by_constraint.constraint_6_staffing_levels}</li>
        </ul>
    </div>
`;

// Render Weekly Hours
const weeklyHoursContainer = document.getElementById('weekly_hours_container');
weeklyHoursContainer.innerHTML = '';
violationsData.constraint_3_weekly_hours.forEach(item => {
    weeklyHoursContainer.innerHTML += `
        <div class="p-4 bg-white border rounded-lg shadow-sm">
            <p><strong>Staff ID:</strong> ${item.staff_id}</p>
            <p><strong>Week:</strong> ${item.week}</p>
            <p><strong>Calculated Hours:</strong> ${item.calculated_hours}</p>
            <p><strong>Target Hours:</strong> ${item.target_hours}</p>
            <p><strong>Difference:</strong> <span class="${item.difference < 0 ? 'text-green-500' : 'text-red-500'}">${item.difference}</span></p>
        </div>
    `;
});

// Render Friday Early Leave
// const fridayEarlyLeaveContainer = document.getElementById('friday_early_leave_container');
// fridayEarlyLeaveContainer.innerHTML = '';
// violationsData.constraint_4_friday_early_leave.forEach(item => {
//     fridayEarlyLeaveContainer.innerHTML += `
//         <div class="p-4 bg-white border rounded-lg shadow-sm">
//             <p><strong>Staff ID:</strong> ${item.staff_id}</p>
//             <p><strong>Violation:</strong> ${item.violation}</p>
//             <p><strong>Friday End Times:</strong> ${item.friday_end_times.join(', ')}</p>
//         </div>
//     `;
// });

const fridayEarlyLeaveContainer = document.getElementById('friday_early_leave_container');
    fridayEarlyLeaveContainer.innerHTML = '';
    violationsData.constraint_4_friday_early_leave.forEach(item => {
        let details = '';
        if (item.early_leave_weeks) {
            details += `<p><strong>Early Leave Weeks:</strong> ${item.early_leave_weeks.join(', ')}</p>`;
        }
        if (item.expected) {
            details += `<p><strong>Expected:</strong> ${item.expected}</p>`;
        }
        if (item.friday_end_time) {
            details += `<p><strong>Friday End Time:</strong> ${item.friday_end_time}</p>`;
        }
        if (item.friday_end_times) {
            details += `<p><strong>Friday End Times:</strong> ${item.friday_end_times.join(', ')}</p>`;
        }
        if (item.week) {
            details += `<p><strong>Week:</strong> ${item.week}</p>`;
        }
        fridayEarlyLeaveContainer.innerHTML += `
            <div class="p-4 bg-white border rounded-lg shadow-sm mb-2">
                <p><strong>Staff ID:</strong> ${item.staff_id}</p>
                <p><strong>Violation:</strong> ${item.violation}</p>
                ${details}
            </div>
        `;
    });

// Render Fixed Schedules
const fixedSchedulesContainer = document.getElementById('fixed_schedules_container');
fixedSchedulesContainer.innerHTML = '';
violationsData.constraint_5_fixed_schedules.forEach(item => {
    fixedSchedulesContainer.innerHTML += `
        <div class="p-4 bg-white border rounded-lg shadow-sm">
            <p><strong>Staff ID:</strong> ${item.staff_id}</p>
            <p><strong>Week:</strong> ${item.week}</p>
            <p><strong>Day:</strong> ${item.day}</p>
            <p><strong>Violation:</strong> ${item.violation}</p>
        </div>
    `;
});

// Render Staffing Levels
const staffingLevelsContainer = document.getElementById('staffing_levels_container');
staffingLevelsContainer.innerHTML = '';
violationsData.constraint_6_staffing_levels.forEach(item => {
    staffingLevelsContainer.innerHTML += `
        <div class="p-4 bg-white border rounded-lg shadow-sm">
            <p><strong>Room:</strong> ${item.room}</p>
            <p><strong>Week:</strong> ${item.week}</p>
            <p><strong>Day:</strong> ${item.day}</p>
            <p><strong>Time Slot:</strong> ${item.time_slot}</p>
            <p><strong>Violation:</strong> ${item.violation}</p>
        </div>
    `;
});
}