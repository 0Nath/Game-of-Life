import cv2
import numpy as np
import pygame


class VideoAssembler:
    def __init__(self, filename, size, fps=30, codec="mp4v"):
        """
        filename : str → ex: "output.mp4"
        size     : (width, height)
        fps      : int
        codec    : str → "mp4v", "XVID", "avc1"
        """
        self.width, self.height = size
        self.fps = fps

        fourcc = cv2.VideoWriter_fourcc(*codec)
        self.writer = cv2.VideoWriter(
            filename,
            fourcc,
            fps,
            (self.width, self.height)
        )

        if not self.writer.isOpened():
            raise RuntimeError("Impossible d'ouvrir le fichier vidéo")

    # ---------- méthodes publiques ----------

    def add_frame(self, image):
        """
        image peut être :
        - numpy array (H, W, 3) RGB ou BGR
        - pygame.Surface
        """

        frame = self._to_bgr_frame(image)
        self.writer.write(frame)

    def close(self):
        self.writer.release()

    # ---------- méthodes internes ----------

    def _to_bgr_frame(self, image):
        # Pygame Surface
        if isinstance(image, pygame.Surface):
            frame = pygame.surfarray.array3d(image)
            frame = np.transpose(frame, (1, 0, 2))
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # NumPy array
        elif isinstance(image, np.ndarray):
            frame = image
            if frame.shape[:2] != (self.height, self.width):
                raise ValueError("Taille de l'image incorrecte")

            # RGB → BGR si nécessaire
            if frame.shape[2] == 3:
                # heuristique simple
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        else:
            raise TypeError("Type d'image non supporté")

        return frame

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_coordinates(self):
        return self.x, self.y

    def __repr__(self):
        return "{Cell: " + str(self.x) + "," + str(self.y)+"}"

class GameOfLife:

    def __init__(self,dimensions,fps = None,ticks = None, shematics = {},record = False):

        pygame.init()
        self.__dimensions = dimensions
        self.__screen = pygame.display.set_mode(self.__dimensions,pygame.RESIZABLE)
        self.__font = pygame.font.SysFont("consolas", max(15, self.__dimensions[0] // 70))
        pygame.display.set_caption("Game of Life")
        self.__record = record
        if self.__record :
            import cv2
            import numpy as np

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
                self.__fps = 60
                self.__ticks = 30
                print(f"Error.\nGoal FPS set to {self.__fps}\nGoal ticks set to {self.__ticks}")

        if self.__fps%self.__ticks != 0:
            print("Ticks should divide FPS evenly. Framerate inaccuracy may occur otherwise.")


        self.__living_cells = []
        self.__living_cells2 = []
        self.__grid = [ [ 0 for _ in range(1000)] for _ in range(1000) ]
        self.__end = False


        self.__zoom = 0.1
        self.__coords = [len(self.__grid)//2,len(self.__grid[0])//2]
        self.__color = (0,0,0) # Cells color
        self.__editing = False
        self.__show_border = False
        self.__shem = shematics


        self.__expantion_rate = 50
        self.__max_grid_size = (4000,4000)

        self.__generation = 0

        if self.__record:
            self.__video = VideoAssembler("video.mp4",self.__dimensions,self.__fps)

        while not self.__end:

            for _ in range(self.__fps//self.__ticks):

                self.__screen.fill((255,255,255))
                self.__last_mouse_pos = pygame.mouse.get_pos()


                self.__handle_events__()
                self.__render__()

                pygame.display.flip()
                if self.__record:
                    self.__video.add_frame(self.__screen)
                self.__fps_clock.tick(self.__fps)
            self.__tick_clock.tick(self.__ticks)

            if not self.__editing:
                if len(self.__living_cells) > 0:
                    self.__generation+=1
                self.__update__()
        if self.__record:
            self.__video.close()

    def __handle_events__(self):
        events = pygame.event.get()
        for event in events:
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
                elif event.key == pygame.K_c:
                    self.__grid = [ [ 0 for _ in range(len(self.__grid[1]))] for _ in range(len(self.__grid)) ]
                elif event.key == pygame.K_f:
                    self.__zoom = 0.1
                    self.__coords = [0, 0]

                elif event.key == pygame.K_s:
                    self.__shem_placer__()

            elif event.type == pygame.QUIT:
                self.__end = True
                print("Quitting...")
            elif event.type == pygame.VIDEORESIZE:
                self.__dimensions = event.size
                self.__screen = pygame.display.set_mode(self.__dimensions, pygame.RESIZABLE)

        x, y = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:

            if self.__editing:  # Place a Cell
                self.__place__(x, y)

            else:  # Move the position.
                x = self.__last_mouse_pos[0] - x
                y = self.__last_mouse_pos[1] - y
                self.__coords[0] += x * self.__zoom
                self.__coords[1] += y * self.__zoom
        elif self.__editing and pygame.mouse.get_pressed()[2]:
            x = self.__last_mouse_pos[0] - x
            y = self.__last_mouse_pos[1] - y
            self.__coords[0] += x * self.__zoom
            self.__coords[1] += y * self.__zoom
        return events

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

            y1 = (0 - self.__coords[1]) / self.__zoom + self.__dimensions[1] / 2
            y2 = (len(self.__grid[0]) - self.__coords[1]) / self.__zoom + self.__dimensions[1] / 2
            x1 = (0 - self.__coords[0]) / self.__zoom + self.__dimensions[0] / 2
            x2 = (len(self.__grid) - self.__coords[0]) / self.__zoom + self.__dimensions[0] / 2
            y1 = max(0,min(y1,len(self.__grid[0])))
            y2 = max(0, min(y2, len(self.__grid[0])))
            x1 = max(0,min(x1,len(self.__grid)))
            x2 = max(0, min(x2, len(self.__grid)))

            for i in range(0,len(self.__grid),grid_spacing):
                x = (i - self.__coords[0]) / self.__zoom + self.__dimensions[0] / 2
                if 0<x<len(self.__grid):
                    pygame.draw.line(self.__screen, self.__color, (x,y1),(x,y2))

            for j in range(0,len(self.__grid[0]),grid_spacing):
                y = (j - self.__coords[1]) / self.__zoom + self.__dimensions[1] / 2
                if 0<y<len(self.__grid[0]):
                    pygame.draw.line(self.__screen, self.__color, (x1,y),(x2,y),)

        if self.__show_border: # Display border
            x1 = (0 - self.__coords[0]) / self.__zoom + self.__dimensions[0] / 2
            x2 = (len(self.__grid) - self.__coords[0]) / self.__zoom + self.__dimensions[0] / 2
            y1 = (0 - self.__coords[1]) / self.__zoom + self.__dimensions[1] / 2
            y2 = (len(self.__grid[1]) - self.__coords[1]) / self.__zoom + self.__dimensions[1] / 2
            pygame.draw.rect(self.__screen,self.__color,(x1,y1,x2-x1,y2-y1),1)

        if len(self.__living_cells)>0:
            tpc = round(self.__tick_clock.get_fps()/len(self.__living_cells),4)
        else:
            tpc = "NA"
        text = self.__font.render(f"FPS: {round(self.__fps_clock.get_fps(),2)}  ticks: {round(self.__tick_clock.get_fps(),2)}  Cells: {len(self.__living_cells)}  ticks/cells:  {tpc}  Grid size: {len(self.__grid)}x{len(self.__grid[1])}  Generations: {self.__generation}", True, (0,0,0))
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
            try:
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
                                    if neighbors_of_dead_cell == 4:
                                        break

                            if neighbors_of_dead_cell == 3 and (cell.x + casex, cell.y + casey) not in added_cell:
                                new_cell = Cell(cell.x + casex, cell.y + casey)
                                self.__living_cells2.append(new_cell)
                                added_cell.append((new_cell.x, new_cell.y))


                    if neighbors == 3 or neighbors == 2 and (cell.x,cell.y) not in added_cell:
                        self.__living_cells2.append(cell)
                        added_cell.append((cell.x,cell.y))
            except IndexError as e:
                print(e)

        for j in self.__living_cells:
            self.__grid[j.x][j.y] = 0
        self.__living_cells = self.__living_cells2[:]
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
        self.__place_cell__(truex,truey)

    def __place_cell__(self,x,y):
        try:
            while (x <= 0 or x >= len(self.__grid)-1) and len(self.__grid) < self.__max_grid_size[0]:

                if x <= 0 :
                    self.__expand__(1,0,0,0)
                    x+=self.__expantion_rate
                if x >= len(self.__grid)-1 :
                    self.__expand__(0,1,0,0)
            while (y <= 0 or y >= len(self.__grid[0])-1) and len(self.__grid[0]) < self.__max_grid_size[1]:
                if y <= 0 :
                    self.__expand__(0,0,1,0)
                    y += self.__expantion_rate
                if y >= len(self.__grid[0])-1 :
                    self.__expand__(0,0,0,1)

            if self.__grid[x][y] == 0 and x>0 and y>0:
                new_cell = Cell(x,y)
                self.__grid[x][y] = new_cell
                self.__living_cells.append(new_cell)

        except Exception as e:
            print(e,x,y)

    def __shem_placer__(self):

        x = round(self.__coords[0])
        y = round(self.__coords[1])
        shem = self.__ask_shematics__()
        for i,row in enumerate(shem):
            for j , item in enumerate(row):
                if item == 1:
                    self.__place_cell__(j+x,i+y)

    def __ask_shematics__(self):
        choice = 0
        position = 0
        running =True
        dic = {}
        for i,name in enumerate(self.__shem):
            dic[i] = name
        rect_x = self.__dimensions[0]/4
        rect_y = self.__dimensions[1]/6

        while running and  not self.__end :
            for _ in range(self.__fps // self.__ticks):


                self.__screen.fill((255,255,255))
                self.__last_mouse_pos = pygame.mouse.get_pos()


                events = self.__handle_events__()
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_UP and position > 0:
                            position -= 1
                        if event.key == pygame.K_DOWN and position < len(self.__shem) - 1:
                            position += 1
                        if event.key == pygame.K_RETURN:
                            choice = position
                            running = False

                self.__render__()
                for i,shem in enumerate(self.__shem.items()):
                    color = (200,200,0) if i == position else (0,0,0)
                    surface = pygame.Surface((rect_x,rect_y*10))
                    self.__draw_Cells__(surface,(rect_x,rect_y),shem,color)
                    self.__screen.blit(surface,(0,rect_y*i))




                pygame.display.flip()
                if self.__record:
                    self.__video.add_frame(self.__screen)
                self.__fps_clock.tick(self.__fps)
            self.__tick_clock.tick(self.__ticks)
            if not self.__editing:
                if len(self.__living_cells) > 0:
                    self.__generation+=1
                self.__update__()



        return self.__shem[dic[choice]]

    def __draw_Cells__(self,surface,size,shem,case_color=(0,0,0)):
        x,y = size
        surface.fill((255,255,255))
        pygame.draw.rect(surface,case_color,(3,3,x-7,y-4),2)

        cell_size = min( round((size[1]/len(shem[1]))*0.70) , round((size[0]//len(shem[1][0]))*0.70) )
        text = self.__font.render(shem[0], True, (0,0,0))
        surface.blit(text, (5, 5))

        x_offset = round( (size[0]/2) - ( len(shem[1][0])*cell_size ) /2  )
        y_offset = round( (size[1]/2) - ( len(shem[1])*cell_size ) /2  )
        for i,row in enumerate(shem[1]):

            for j,element in enumerate(row):
                if element == 1:
                    pygame.draw.rect(surface,(0,0,0),( (j*cell_size)+x_offset,(i*cell_size)+y_offset,cell_size,cell_size),0)
        return 1


glider = [
    [0,1,0],
    [0,0,1],
    [1,1,1],
]

glider_canon = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
    [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
    [1,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [1,1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1,1,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

spinning_thing = [
    [1,1,1,0,1],
    [1,0,0,0,0],
    [0,0,0,1,1],
    [0,1,1,0,1],
    [1,0,1,0,1],

]

puffer1 = [
    [0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [0, 1, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 1, 1, 0],
    [0, 0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0,0,0,0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 0],
    [0, 0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 1, 1, 0],
    [0, 0, 0, 0, 1, 0, 0],
    [1, 1, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 1, 0]
]

rake
cube = [ ]
for i in range(200):
    l = []
    for j in range(200):
        l.append(1)
    cube.append(l)
shematics = {"Glider":glider , "Glider Canon":glider_canon , "Spinning thing":spinning_thing , "Puffer 1":puffer1 , "cube":cube}

if __name__ == '__main__':
    GameOfLife((800,600),500,500,shematics,False)