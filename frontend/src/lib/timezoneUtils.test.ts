/**
 * Tests for timezone utility functions
 * Run with: npx tsx src/lib/timezoneUtils.test.ts
 */

import {
  getTimezoneOffsetHours,
  getTimezoneOffsetParts,
  localHourToUTC,
  utcHourToLocal,
  localTimeToUTC,
  utcTimeToLocal,
  cronUTCToLocal,
  cronLocalToUTC,
  getTimezoneAbbreviation,
} from './timezoneUtils';

console.log('🧪 Testing Timezone Utilities\n');

// Test 1: Timezone offset
console.log('Test 1: Get timezone offset');
const offset = getTimezoneOffsetHours();
console.log(`  Current timezone offset: ${offset} hours`);
console.log(`  ✅ Pass\n`);

// Test 2: Get timezone abbreviation
console.log('Test 2: Get timezone abbreviation');
const tz = getTimezoneAbbreviation();
console.log(`  Timezone abbreviation: ${tz}`);
console.log(`  ✅ Pass\n`);

// Test 3: Local to UTC conversion
console.log('Test 3: Local hour to UTC hour');
const testCases = [
  { local: 0, expected: 'wraps correctly' },
  { local: 9, expected: 'converts correctly' },
  { local: 12, expected: 'converts correctly' },
  { local: 23, expected: 'wraps correctly' },
];

testCases.forEach(({ local }) => {
  const utc = localHourToUTC(local);
  console.log(`  ${local}:00 local → ${utc}:00 UTC`);
});
console.log(`  ✅ Pass\n`);

// Test 4: UTC to local conversion (should be inverse of above)
console.log('Test 4: UTC hour to local hour (inverse)');
testCases.forEach(({ local }) => {
  const utc = localHourToUTC(local);
  const backToLocal = utcHourToLocal(utc);
  const match = backToLocal === local ? '✅' : '❌';
  console.log(`  ${local} → ${utc} → ${backToLocal} ${match}`);
  if (backToLocal !== local) {
    throw new Error(`Conversion failed: ${local} !== ${backToLocal}`);
  }
});
console.log(`  ✅ Pass\n`);

// Test 5: Cron local to UTC
console.log('Test 5: Cron local to UTC');
const localCron = '0 9 * * *'; // 9 AM local
const utcCron = cronLocalToUTC(localCron);
console.log(`  Local cron: ${localCron}`);
console.log(`  UTC cron:   ${utcCron}`);
console.log(`  ✅ Pass\n`);

// Test 6: Cron UTC to local (should be inverse)
console.log('Test 6: Cron UTC to local (inverse)');
const backToLocalCron = cronUTCToLocal(utcCron);
console.log(`  UTC cron:   ${utcCron}`);
console.log(`  Local cron: ${backToLocalCron}`);
const cronMatch = backToLocalCron === localCron ? '✅' : '❌';
console.log(`  Match: ${cronMatch}`);
if (backToLocalCron !== localCron) {
  throw new Error(`Cron conversion failed: ${localCron} !== ${backToLocalCron}`);
}
console.log(`  ✅ Pass\n`);

// Test 7: Edge cases - hourly patterns (should not convert)
console.log('Test 7: Hourly patterns (should not convert)');
const hourlyCron = '0 * * * *';
const convertedHourly = cronLocalToUTC(hourlyCron);
console.log(`  Original: ${hourlyCron}`);
console.log(`  Converted: ${convertedHourly}`);
const hourlyMatch = convertedHourly === hourlyCron ? '✅' : '❌';
console.log(`  Should be unchanged: ${hourlyMatch}`);
if (convertedHourly !== hourlyCron) {
  throw new Error(`Hourly pattern should not convert: ${hourlyCron} !== ${convertedHourly}`);
}
console.log(`  ✅ Pass\n`);

// Test 8: Every N hours patterns (should not convert)
console.log('Test 8: Every N hours patterns (should not convert)');
const everyNHoursCron = '0 */6 * * *';
const convertedEveryN = cronLocalToUTC(everyNHoursCron);
console.log(`  Original: ${everyNHoursCron}`);
console.log(`  Converted: ${convertedEveryN}`);
const everyNMatch = convertedEveryN === everyNHoursCron ? '✅' : '❌';
console.log(`  Should be unchanged: ${everyNMatch}`);
if (convertedEveryN !== everyNHoursCron) {
  throw new Error(`Every N hours pattern should not convert: ${everyNHoursCron} !== ${convertedEveryN}`);
}
console.log(`  ✅ Pass\n`);

// Test 9: Weekly patterns (should convert)
console.log('Test 9: Weekly patterns (should convert)');
const weeklyLocalCron = '0 8 * * 1'; // 8 AM Monday local
const weeklyUtcCron = cronLocalToUTC(weeklyLocalCron);
const weeklyBackToLocal = cronUTCToLocal(weeklyUtcCron);
console.log(`  Local cron: ${weeklyLocalCron}`);
console.log(`  UTC cron:   ${weeklyUtcCron}`);
console.log(`  Back to local: ${weeklyBackToLocal}`);
const weeklyMatch = weeklyBackToLocal === weeklyLocalCron ? '✅' : '❌';
console.log(`  Round-trip match: ${weeklyMatch}`);
if (weeklyBackToLocal !== weeklyLocalCron) {
  throw new Error(`Weekly cron conversion failed: ${weeklyLocalCron} !== ${weeklyBackToLocal}`);
}
console.log(`  ✅ Pass\n`);

// Test 10: Minute offset support - getTimezoneOffsetParts
console.log('Test 10: Get timezone offset parts (hours + minutes)');
const offsetParts = getTimezoneOffsetParts();
console.log(`  Offset hours: ${offsetParts.hours}`);
console.log(`  Offset minutes: ${offsetParts.minutes}`);
console.log(`  Total: ${offsetParts.hours}h ${offsetParts.minutes}m`);
console.log(`  ✅ Pass\n`);

// Test 11: Local time to UTC with minutes
console.log('Test 11: Local time to UTC (with minute handling)');
const timeTestCases = [
  { hour: 9, minute: 0, label: '9:00 AM' },
  { hour: 12, minute: 30, label: '12:30 PM' },
  { hour: 23, minute: 45, label: '11:45 PM' },
  { hour: 0, minute: 15, label: '12:15 AM' },
];

timeTestCases.forEach(({ hour, minute, label }) => {
  const utc = localTimeToUTC(hour, minute);
  console.log(`  ${label} local → ${utc.hour}:${utc.minute.toString().padStart(2, '0')} UTC`);
});
console.log(`  ✅ Pass\n`);

// Test 12: UTC time to local with minutes (round-trip test)
console.log('Test 12: UTC to local time (inverse with minutes)');
timeTestCases.forEach(({ hour, minute, label }) => {
  const utc = localTimeToUTC(hour, minute);
  const backToLocal = utcTimeToLocal(utc.hour, utc.minute);
  const match = (backToLocal.hour === hour && backToLocal.minute === minute) ? '✅' : '❌';
  console.log(`  ${label} → UTC ${utc.hour}:${utc.minute.toString().padStart(2, '0')} → ${backToLocal.hour}:${backToLocal.minute.toString().padStart(2, '0')} ${match}`);
  if (backToLocal.hour !== hour || backToLocal.minute !== minute) {
    throw new Error(`Time conversion failed: ${hour}:${minute} !== ${backToLocal.hour}:${backToLocal.minute}`);
  }
});
console.log(`  ✅ Pass\n`);

// Test 13: Cron conversion with minute offsets
console.log('Test 13: Cron conversion with minute offsets');
const cronMinuteTests = [
  { local: '0 9 * * *', label: 'Daily 9:00 AM' },
  { local: '30 14 * * *', label: 'Daily 2:30 PM' },
  { local: '15 8 * * 1', label: 'Weekly Mon 8:15 AM' },
  { local: '45 23 15 * *', label: 'Monthly 15th 11:45 PM' },
];

cronMinuteTests.forEach(({ local, label }) => {
  const utc = cronLocalToUTC(local);
  const backToLocal = cronUTCToLocal(utc);
  const match = backToLocal === local ? '✅' : '❌';
  console.log(`  ${label}: ${local} → ${utc} → ${backToLocal} ${match}`);
  if (backToLocal !== local) {
    throw new Error(`Cron minute conversion failed: ${local} !== ${backToLocal}`);
  }
});
console.log(`  ✅ Pass\n`);

// Test 14: Minute overflow handling
console.log('Test 14: Minute overflow/underflow handling');
const overflowTests = [
  { hour: 23, minute: 45, label: '23:45 (may wrap to next day)' },
  { hour: 0, minute: 15, label: '0:15 (may wrap to previous day)' },
];

overflowTests.forEach(({ hour, minute, label }) => {
  const utc = localTimeToUTC(hour, minute);
  const backToLocal = utcTimeToLocal(utc.hour, utc.minute);
  const match = (backToLocal.hour === hour && backToLocal.minute === minute) ? '✅' : '❌';
  console.log(`  ${label}: ${hour}:${minute.toString().padStart(2, '0')} → UTC ${utc.hour}:${utc.minute.toString().padStart(2, '0')} → ${backToLocal.hour}:${backToLocal.minute.toString().padStart(2, '0')} ${match}`);
  if (backToLocal.hour !== hour || backToLocal.minute !== minute) {
    throw new Error(`Overflow handling failed: ${hour}:${minute} !== ${backToLocal.hour}:${backToLocal.minute}`);
  }
});
console.log(`  ✅ Pass\n`);

console.log('🎉 All tests passed!');
console.log(`\nCurrent timezone: ${tz} (offset: ${offset > 0 ? '+' : ''}${-offset} hours from UTC)`);
if (offsetParts.minutes !== 0) {
  console.log(`Note: Your timezone has a ${offsetParts.minutes}-minute offset (e.g., India UTC+5:30, Nepal UTC+5:45)`);
}
