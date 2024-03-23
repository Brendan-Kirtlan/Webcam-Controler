import math

def read_and_print(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            return content
    except Exception as e:
        print(f"Error: {e}")
        
path = r"path here"
dist_pairs = [20,19,4,0,8,0,12,0,16,0,20,0]
dists = [[],[],[],[],[],[]]
avg_dists = []
norm_dists = []

#gets distances for the pairs array
def calc_dists(points):
    i = 0
    arr_ind = 0
    while i < (len(dist_pairs) - 1):
        distance = math.sqrt((points[dist_pairs[i]*3] - points[dist_pairs[i+1]*3])**2 + (points[dist_pairs[i]*3 + 1] - points[dist_pairs[i+1]*3 + 1])**2 + (points[dist_pairs[i]*3 + 2] - points[dist_pairs[i+1]*3 + 2])**2)
        dists[arr_ind].append(distance)
        i += 2
        arr_ind += 1
        
        
    return 0

def average_dists():
    for sub in dists:
         avg_dists.append(sum(sub)/len(sub))

def normalize_dists():
    i = 1
    while i < len(avg_dists):
        norm_dists.append(avg_dists[i] / avg_dists[0])
        i += 1
        

def main():
    file_index = 0
    while file_index < 6:
        content = read_and_print(path + "\output" + str(file_index) + ".txt")
        content = content.replace('\n', ',')
        point_arr = content.split(',')
        point_arr.pop()
        point_arr = [float(value) for value in point_arr]
        calc_dists(point_arr)
        file_index += 1
    average_dists()
    
    for sub in dists:
        print(sub)
    print(avg_dists)
    
    normalize_dists()
    print(norm_dists)

if __name__ == "__main__":
    main()