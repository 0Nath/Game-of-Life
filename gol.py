import pygame



class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_coordinates(self):
        return self.x, self.y

    def __repr__(self):
        return "{Cell: " + str(self.x) + "," + str(self.y)+"}"


class GameOfLife:

    def __init__(self,dimensions,fps = None,ticks = None):

        pygame.init()
        self.__dimensions = dimensions
        self.__screen = pygame.display.set_mode(self.__dimensions)
        self.__font = pygame.font.SysFont("consolas", max(15, self.__dimensions[0] // 70))
        pygame.display.set_caption("Game of Life")

        self.__tick_clock = pygame.time.Clock()
        self.__fps_clock = pygame.time.Clock()
        self.__last_mouse_pos = pygame.mouse.get_pos()

        self.__fps = fps
        self.__ticks = ticks
        if self.__fps == None or self.__ticks == None:
            try:
                self.__fps = int(input("Goal FPS: "))
                self.__ticks = int(input("Goal ticks: "))
                if self.__fps <= 0 or self.__ticks <= 0 or self.__fps % self.__ticks != 0 or self.__fps>self.__ticks:
                    print("\nFPS must be higher than zero.\nFPS and ticks must higher than 0.\n")
                    raise SyntaxError
            except:
                print(f"Error.\nGoal FPS set to {self.__fps}\nGoal ticks set to {self.__ticks}")

        if self.__fps%self.__ticks != 0:
            print("Ticks should divide FPS evenly. Framerate inaccuracy may occur otherwise.")


        self.__zoom = 0.1
        self.__coords = [0,0]
        self.__color = (0,0,0) # Cells color
        self.__editing = False
        self.__show_border = False

        self.__living_cells = []
        self.__living_cells2 = []
        self.__grid = [ [ 0 for _ in range(100)] for _ in range(100) ]
        self.__end = False

        self.__expantion_rate = 50
        self.__max_grid_size = (2000,2000)

        self.__generation = 0

        while not self.__end:

            for _ in range(self.__fps//self.__ticks):

                self.__screen.fill((255,255,255))
                self.__last_mouse_pos = pygame.mouse.get_pos()

                for event in pygame.event.get():
                    if event.type == pygame.MOUSEWHEEL:
                        if event.y < 0:
                            self.__zoom *= 0.90
                        elif event.y > 0:
                            self.__zoom *= 1.1

                    if event.type == pygame.KEYDOWN:

                        if event.key == pygame.K_SPACE:
                            if self.__editing:
                                self.__editing = False
                            else:
                                self.__editing = True

                        elif event.key == pygame.K_g:
                            self.__show_border = True if not self.__show_border else False

                        elif event.key == pygame.K_f:
                            self.__zoom = 0.1
                            self.__coords = [0,0]

                    elif event.type == pygame.QUIT:
                        self.__end = True
                        print("Quitting...")

                if pygame.mouse.get_pressed()[0]:
                    x, y = pygame.mouse.get_pos()

                    if self.__editing: # Place a Cell
                        self.__place__(x,y)

                    else: # Move the position.
                        x = self.__last_mouse_pos[0] - x
                        y = self.__last_mouse_pos[1] - y
                        self.__coords[0] += x * self.__zoom
                        self.__coords[1] += y * self.__zoom

                self.__render__()
                pygame.display.flip()

                self.__fps_clock.tick(self.__fps)
            self.__tick_clock.tick(self.__ticks)

            if not self.__editing:
                if len(self.__living_cells) > 0:
                    self.__generation+=1
                self.__update__()



    def __render__(self):
        """
        render cells, grid, and border
        :return:
        """
        for i in self.__living_cells: # Compute relative position and draw it
            x = (i.x-self.__coords[0]) / self.__zoom + self.__dimensions[0] / 2
            y = (i.y-self.__coords[1]) / self.__zoom + self.__dimensions[1] / 2
            pygame.draw.rect(self.__screen, self.__color, (x-1,y-1,(1/self.__zoom)+1,(1/self.__zoom)+1))

        if self.__editing: # Display grid

            grid_spacing = max(round(self.__zoom*10),1)


            for i in range(0,len(self.__grid),grid_spacing):
                x = (i - self.__coords[0]) / self.__zoom + self.__dimensions[0] / 2
                if x > self.__dimensions[0]:
                    break

                y1=(0 - self.__coords[1]) / self.__zoom + self.__dimensions[1] / 2
                y2=(len(self.__grid[0]) - self.__coords[1]) / self.__zoom + self.__dimensions[1] / 2
                pygame.draw.line(self.__screen, self.__color, (x,y1),(x,y2))

            for j in range(0,len(self.__grid[0]),grid_spacing):
                y = (j - self.__coords[1]) / self.__zoom + self.__dimensions[1] / 2
                if y > self.__dimensions[1]:
                    break

                x1=(0 - self.__coords[0]) / self.__zoom + self.__dimensions[0] / 2
                x2=(len(self.__grid) - self.__coords[0]) / self.__zoom + self.__dimensions[0] / 2
                pygame.draw.line(self.__screen, self.__color, (x1,y),(x2,y),)

        if self.__show_border: # Display border
            x1 = (0 - self.__coords[0]) / self.__zoom + self.__dimensions[0] / 2
            x2 = (len(self.__grid) - self.__coords[0]) / self.__zoom + self.__dimensions[0] / 2
            y1 = (0 - self.__coords[1]) / self.__zoom + self.__dimensions[1] / 2
            y2 = (len(self.__grid[1]) - self.__coords[1]) / self.__zoom + self.__dimensions[1] / 2
            pygame.draw.rect(self.__screen,self.__color,(x1,y1,x2-x1,y2-y1),1)

        text = self.__font.render(f"FPS: {round(self.__fps_clock.get_fps(),2)}  ticks: {round(self.__tick_clock.get_fps(),2)}  Cells: {len(self.__living_cells)}  Grid size: {len(self.__grid)}x{len(self.__grid[1])}  Generation{"" if self.__generation == 0 else "s" }: {self.__generation}", True, (0,0,0))
        self.__screen.blit(text, (10, 10))

    def __update__(self):
        """
        Kill or make new cells
        :return:
        """
        for i in self.__living_cells: #Expand grid if needed
            if len(self.__grid)<self.__max_grid_size[0]:
                if i.x<10 :
                    self.__expand__(1,0,0,0)
                if i.x > len(self.__grid)-10 :
                    self.__expand__(0, 1, 0, 0)
            if len(self.__grid[0]) < self.__max_grid_size[1]:
                if i.y<10 :
                    self.__expand__(0, 0, 1, 0)
                if i.y>len(self.__grid[0])-10 :
                    self.__expand__(0, 0, 0, 1)

        self.__living_cells2 = []



        coords_to_check = (
            (-1, -1), (0, -1), (1, -1),
            (-1, 0), (1, 0),
            (-1, 1), (0, 1), (1, 1)
        )

        added_cell = []
        for cell in self.__living_cells:
            if cell.x > 5 and cell.x < len(self.__grid)-5 and cell.y>5 and cell.y < len(self.__grid[0])-5:
                neighbors = 0

                for casex,casey in coords_to_check:
                    if self.__grid[ cell.x + casex ][ cell.y + casey ] != 0:
                        neighbors += 1


                    if self.__grid[cell.x + casex ][cell.y + casey ] == 0 :
                        neighbors_of_dead_cell = 0
                        for x,y in coords_to_check:
                            if self.__grid[cell.x + casex + x ][cell.y + casey + y ] != 0:
                                neighbors_of_dead_cell += 1
                        if neighbors_of_dead_cell == 3 and (cell.x + casex, cell.y + casey) not in added_cell:
                            new_cell = Cell(cell.x + casex, cell.y + casey)
                            self.__living_cells2.append(new_cell)
                            added_cell.append((new_cell.x, new_cell.y))


                if neighbors == 3 or neighbors == 2 and (cell.x,cell.y) not in added_cell:
                    self.__living_cells2.append(cell)
                    added_cell.append((cell.x,cell.y))

        self.__living_cells = self.__living_cells2[:]
        self.__grid = [ [0] * len(self.__grid[0])  for _ in range(len(self.__grid)) ]
        for i in self.__living_cells:
            if self.__grid[i.x][i.y] == 0 :
                self.__grid[ i.x ][ i.y ] = i


    def __expand__(self,x0,x,y0,y):
        """
        expand the grid in different directions
        :param x0: expand left
        :param x: expand right
        :param y0: expand up
        :param y: expand down
        :return:
        """
        if x0:
            self.__coords[0] += self.__expantion_rate
            for i in self.__living_cells:
                i.x += self.__expantion_rate
        if y0:
            self.__coords[1] += self.__expantion_rate
            for i in self.__living_cells:
                i.y += self.__expantion_rate


        for j in range(len(self.__grid)):
            if y0 and  y:
                self.__grid[j] = [ 0 for _ in range(self.__expantion_rate) ] + self.__grid[j] + [ 0 for _ in range(self.__expantion_rate) ]
            elif y0:
                self.__grid[j] = [0 for _ in range(self.__expantion_rate)] + self.__grid[j]
            elif y:
                self.__grid[j] = self.__grid[j] + [0 for _ in range(self.__expantion_rate)]

        if x0 and x:
            self.__grid = [[0 for _ in range(self.__expantion_rate * 2 + len(self.__grid[0]))] for _ in range(self.__expantion_rate)] + self.__grid + [ [0 for _ in range(self.__expantion_rate * 2 + len(self.__grid[0]))] for _ in range(self.__expantion_rate)]
        elif x0:
            self.__grid = [[0 for _ in range(self.__expantion_rate * 2 + len(self.__grid[0]))] for _ in range(self.__expantion_rate)] + self.__grid
        elif x:
            self.__grid =  self.__grid + [[ 0 for _ in range(self.__expantion_rate*2 + len(self.__grid[0])) ] for _ in range(self.__expantion_rate) ]



    def __place__(self,x,y):
        """
        Place a cell at the coordinates x and y
        :param x:
        :param y:
        :return:
        """

        truex = round((x - self.__dimensions[0] / 2)*self.__zoom+self.__coords[0]-0.5)
        truey = round((y - self.__dimensions[1] / 2)*self.__zoom+self.__coords[1]-0.5)
        try:
            while (truex <= 0 or truex >= len(self.__grid)-1) and len(self.__grid) < self.__max_grid_size[0]:

                if truex <= 0 :
                    self.__expand__(1,0,0,0)
                    truex+=self.__expantion_rate
                if truex >= len(self.__grid)-1 :
                    self.__expand__(0,1,0,0)
            while (truey <= 0 or truey >= len(self.__grid[0])-1) and len(self.__grid[0]) < self.__max_grid_size[1]:
                if truey <= 0 :
                    self.__expand__(0,0,1,0)
                    truey += self.__expantion_rate
                if truey >= len(self.__grid[0])-1 :
                    self.__expand__(0,0,0,1)

            if self.__grid[truex][truey] == 0 and truex>0 and truey>0:
                new_cell = Cell(truex,truey)
                self.__grid[truex][truey] = new_cell
                self.__living_cells.append(new_cell)

        except Exception as e:
            print(e)

if __name__ == '__main__':
    GameOfLife((800,600),50,11)