/** Interfaces for the menu bar. */

/**
 * Represents an option that is selectable from thje menu-bar.
 * @property: name: Name of the option.
 * @property tabIcon: Icon to show for the menu.
 */
export abstract class MenuOption {
    abstract readonly tabIcon: string;
    abstract readonly name: string;
}
