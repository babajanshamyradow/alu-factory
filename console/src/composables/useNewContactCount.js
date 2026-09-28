import { ref } from 'vue'

import { getContactMessageCounts } from '@/api/contactMessages'

// Shared "new contact messages" count for the sidebar badge. The layout
// polls it; the messages screen calls refresh() after changing statuses.
const newCount = ref(0)

async function refresh() {
  try {
    const { data } = await getContactMessageCounts()
    if (data.status === 'SUCCESS') newCount.value = data.result?.new ?? 0
  } catch {
    // Keep the last known value; the badge is only a hint.
  }
}

// Lets a screen that already has fresh counts skip the extra request.
function setCount(value) {
  newCount.value = value
}

export function useNewContactCount() {
  return { newCount, refresh, setCount }
}
