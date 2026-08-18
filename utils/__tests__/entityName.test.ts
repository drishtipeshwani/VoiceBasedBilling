import {
  entityNamesMatch,
  normalizeEntityName,
} from '../entityName';

describe('normalizeEntityName', () => {
  it('trims and collapses whitespace', () => {
    expect(normalizeEntityName('  Ramesh   Kumar  ')).toBe('Ramesh Kumar');
  });

  it('treats case and spacing as the same name', () => {
    expect(entityNamesMatch('ramesh', '  Ramesh ')).toBe(true);
    expect(entityNamesMatch('pens', 'notebooks')).toBe(false);
  });
});
