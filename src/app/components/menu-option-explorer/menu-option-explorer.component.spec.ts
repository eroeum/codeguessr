import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MenuOptionExplorerComponent } from './menu-option-explorer.component';

describe('MenuOptionExplorerComponent', () => {
  let component: MenuOptionExplorerComponent;
  let fixture: ComponentFixture<MenuOptionExplorerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MenuOptionExplorerComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(MenuOptionExplorerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
