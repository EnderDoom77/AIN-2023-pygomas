conda activate pygomas
pygomas manager -j manager_mfabgom@gtirouter.dsic.upv.es -sj service_mfabgom@gtirouter.dsic.upv.es -np 10 -m map_arena
pygomas manager -j manager_mfabgom@localhost -p secret -sj service_mfabgom@localhost -sp secret -np 10 -m map_arena