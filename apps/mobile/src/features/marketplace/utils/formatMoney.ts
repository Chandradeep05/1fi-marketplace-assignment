/**
 * Formats integer paisa to Indian Rupee display string.
 * Strictly presentational. Never used for authoritative calculations.
 *
 * Example:
 * formatPaisa(13490000) -> "₹1,34,900"
 * formatPaisa(800000)   -> "₹8,000"
 * formatPaisa(352500)   -> "₹3,525"
 */
export const formatPaisa = (paisa: number): string => {
  const rupees = Math.floor(paisa / 100);
  return '₹' + rupees.toLocaleString('en-IN');
};

export const formatSavings = (mrpPaisa?: number | null, basePricePaisa?: number): string | null => {
  if (!mrpPaisa || !basePricePaisa || mrpPaisa <= basePricePaisa) {
    return null;
  }
  const diff = mrpPaisa - basePricePaisa;
  return `You save ${formatPaisa(diff)}`;
};
