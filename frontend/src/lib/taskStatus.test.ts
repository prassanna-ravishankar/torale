/**
 * Tests for task status logic module
 * Run with: npx ts-node src/lib/taskStatus.test.ts
 */

import { getTaskStatus, TaskActivityState, type TaskStatusInfo } from './taskStatus';

const GREEN = '\x1b[92m';
const RED = '\x1b[91m';
const BLUE = '\x1b[94m';
const RESET = '\x1b[0m';

function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function testTaskStatusActive(): boolean {
  console.log(`${BLUE}Testing active task status...${RESET}`);

  // Active task
  const status = getTaskStatus('active');
  assert(status.activityState === TaskActivityState.ACTIVE, 'Active task state incorrect');
  assert(status.iconName === 'Activity', 'Active task icon incorrect');
  assert(status.label === 'Monitoring', 'Active task label incorrect');
  assert(status.color === 'green', 'Active task color incorrect');
  console.log(`${GREEN}✓ Active task status correct${RESET}`);

  return true;
}

function testTaskStatusCompleted(): boolean {
  console.log(`\n${BLUE}Testing completed task status...${RESET}`);

  // Completed task
  const status = getTaskStatus('completed');
  assert(
    status.activityState === TaskActivityState.COMPLETED,
    'Completed task state incorrect'
  );
  assert(status.iconName === 'CheckCircle', 'Completed task icon incorrect');
  assert(status.label === 'Completed', 'Completed task label incorrect');
  assert(status.color === 'blue', 'Completed task color incorrect');
  assert(
    status.description.toLowerCase().includes('auto-stopped'),
    'Completed task description incorrect'
  );
  console.log(`${GREEN}✓ Completed task status correct${RESET}`);

  return true;
}

function testTaskStatusPaused(): boolean {
  console.log(`\n${BLUE}Testing paused task status...${RESET}`);

  // Paused task
  const status = getTaskStatus('paused');
  assert(status.activityState === TaskActivityState.PAUSED, 'Paused task state incorrect');
  assert(status.iconName === 'Pause', 'Paused task icon incorrect');
  assert(status.label === 'Paused', 'Paused task label incorrect');
  assert(status.color === 'yellow', 'Paused task color incorrect');
  console.log(`${GREEN}✓ Paused task status correct${RESET}`);

  return true;
}

function testTaskActivityStateEnum(): boolean {
  console.log(`\n${BLUE}Testing TaskActivityState enum...${RESET}`);

  assert(TaskActivityState.ACTIVE === 'active', 'ACTIVE enum value incorrect');
  assert(TaskActivityState.COMPLETED === 'completed', 'COMPLETED enum value incorrect');
  assert(TaskActivityState.PAUSED === 'paused', 'PAUSED enum value incorrect');
  console.log(`${GREEN}✓ TaskActivityState enum values correct${RESET}`);

  // Test all states are unique
  const states = [TaskActivityState.ACTIVE, TaskActivityState.COMPLETED, TaskActivityState.PAUSED];
  const uniqueStates = new Set(states);
  assert(uniqueStates.size === 3, 'Activity states are not unique');
  console.log(`${GREEN}✓ All activity states are unique${RESET}`);

  return true;
}

function testStatusInfoStructure(): boolean {
  console.log(`\n${BLUE}Testing status info structure...${RESET}`);

  const status = getTaskStatus('active');

  // Check all required fields exist
  const requiredFields: (keyof TaskStatusInfo)[] = [
    'activityState',
    'iconName',
    'label',
    'color',
    'description',
  ];
  for (const field of requiredFields) {
    assert(field in status, `Missing field: ${field}`);
    assert(status[field] !== null && status[field] !== undefined, `Field ${field} is null/undefined`);
  }
  console.log(`${GREEN}✓ All required fields present${RESET}`);

  // Check field types
  assert(typeof status.iconName === 'string', 'iconName is not a string');
  assert(typeof status.label === 'string', 'label is not a string');
  assert(typeof status.color === 'string', 'color is not a string');
  assert(typeof status.description === 'string', 'description is not a string');
  console.log(`${GREEN}✓ All field types correct${RESET}`);

  return true;
}

function main(): boolean {
  console.log(`${BLUE}${'='.repeat(60)}${RESET}`);
  console.log(`${BLUE}Task Status Module Tests (Frontend)${RESET}`);
  console.log(`${BLUE}${'='.repeat(60)}${RESET}`);

  let allPass = true;

  try {
    allPass = testTaskActivityStateEnum() && allPass;
    allPass = testTaskStatusActive() && allPass;
    allPass = testTaskStatusCompleted() && allPass;
    allPass = testTaskStatusPaused() && allPass;
    allPass = testStatusInfoStructure() && allPass;
  } catch (error) {
    console.error(`${RED}✗ Test failed: ${error}${RESET}`);
    allPass = false;
  }

  console.log(`\n${BLUE}${'='.repeat(60)}${RESET}`);
  if (allPass) {
    console.log(`${GREEN}✅ All task_status tests passed!${RESET}`);
  } else {
    console.log(`${RED}❌ Some tests failed${RESET}`);
  }
  console.log(`${BLUE}${'='.repeat(60)}${RESET}`);

  return allPass;
}

// Run tests if this file is executed directly
const success = main();
process.exit(success ? 0 : 1);
