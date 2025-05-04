import { ref, computed, reactive } from 'vue';

interface MenuItemState {
  isOpen: boolean;
  title: string;
  content: any;
  position: {
    x: number;
    y: number;
  } | null;
}

// Singleton state for managing menu items
const activeMenuItem = ref<MenuItemState | null>(null);

export function useMenuItems() {
  // Open a menu item
  const openMenuItem = (title: string, content: any, position: { x: number, y: number } | null = null) => {
    activeMenuItem.value = {
      isOpen: true,
      title,
      content,
      position
    };
  };

  // Close the active menu item
  const closeMenuItem = () => {
    if (activeMenuItem.value) {
      activeMenuItem.value.isOpen = false;
      // Allow time for animation to complete before removing
      setTimeout(() => {
        activeMenuItem.value = null;
      }, 300);
    }
  };

  // Check if a specific menu item is active
  const isMenuItemActive = (title: string) => {
    return activeMenuItem.value?.title === title && activeMenuItem.value?.isOpen;
  };

  return {
    activeMenuItem: computed(() => activeMenuItem.value),
    openMenuItem,
    closeMenuItem,
    isMenuItemActive
  };
}