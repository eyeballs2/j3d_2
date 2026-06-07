                        wh = max(1, int(WALL_HEIGHT_MULTIPLIER / (dist + PARTICLE_EPSILON)))
                        
                        col_s = pygame.transform.scale(wall_slice, (int(WIDTH/NUM_RAYS)+1, wh))
                        m = max(0, min(255, total_light)) / 255.0
                        col_s.fill((int(m*255), int(m*255), int(m*255)), special_flags=pygame.BLEND_RGB_MULT)
                        
                        # FIX: Wall positioning - walls now rest on the floor (HEIGHT//2) instead of floating
                        # Calculate top position so wall base aligns with floor line
                        wall_top = (HEIGHT // 2) - (wh // 2)
                        wall_bottom = (HEIGHT // 2) + (wh // 2)
                        
                        self.screen.blit(col_s, (ray * (WIDTH / NUM_RAYS), wall_top))
                        break
