/**
 * resources.js
 * ------------
 * Where a person can actually turn.
 *
 * The system tells someone their words suggest distress and then advises them
 * to speak to a professional. Advice of that kind is worth very little without
 * somewhere to go, and the moment a person reads a distress result is the
 * moment they are least able to start searching. The contacts are therefore
 * held here, in one place, and shown at that moment.
 *
 * These numbers were checked against three independent published sources in
 * August 2026 (LifeLine International, findahelpline.com and the Nigerian
 * Mental Health directory). Helpline numbers change. Verify them again before
 * the system is shown to anyone, and do not remove a line without replacing
 * it: a broken number is worse than a plainly absent one.
 */

export const HELPLINES = [
  {
    name: "SURPIN, Suicide Research and Prevention Initiative",
    tel: "08000787746",
    display: "0800 078 7746",
    note: "Free to call, 24 hours. Depression, anxiety, substance use and suicidal thoughts.",
  },
  {
    name: "Mentally Aware Nigeria Initiative (MANI)",
    tel: "08091116264",
    display: "0809 111 6264",
    note: "24 hours.",
  },
  {
    name: "Emergency services",
    tel: "112",
    display: "112",
    note: "If you or someone near you is in immediate danger.",
  },
];

/**
 * The on-campus route.
 *
 * TODO before the system is used or demonstrated: replace `tel` and `display`
 * with the real extension for Counselling and Psychological Services or the
 * Medical Centre. The university publishes the service but not a number, and
 * an invented one would be worse than none, so the entry currently tells a
 * student where to go rather than what to dial. If you cannot obtain a number,
 * leave `tel` empty — the interface renders the entry either way.
 */
export const CAMPUS = {
  name: "University of Nigeria, Nsukka",
  tel: "",
  display: "",
  note: "Counselling and Psychological Services, and the University Medical Centre, are both open to registered students.",
};
