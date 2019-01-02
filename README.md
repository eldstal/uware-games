# uware-games
A set of games for [uWare](https://github.com/eldstal/uware)

To play these games in the launcher, add the following line to `repos.json`:
```
{
   ...
   "eldstal": "https://github.com/eldstal/uware-games"
}
```

To play outside the launcher, just clone the repo and run `build` to compile and then
invoke any one of the games' `run` executable from inside the game's directory

```
$ ./build
$ cd splash
$ ./run
```
