/** Canonical shop entity name: trim and collapse inner whitespace. */
export function normalizeEntityName(name: string): string {
  return name.trim().replace(/\s+/g, ' ');
}

export function entityNameKey(name: string): string {
  return normalizeEntityName(name).toLocaleLowerCase('en');
}

export function entityNamesMatch(left: string, right: string): boolean {
  return entityNameKey(left) === entityNameKey(right);
}
