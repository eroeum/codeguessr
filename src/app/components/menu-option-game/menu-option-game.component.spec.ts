import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MenuOptionGameComponent } from './menu-option-game.component';

describe('MenuOptionGameComponent', () => {
  let component: MenuOptionGameComponent;
  let fixture: ComponentFixture<MenuOptionGameComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MenuOptionGameComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(MenuOptionGameComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
