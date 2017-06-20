using System.Collections;
using System.Collections.Generic;
using UnityEngine;


public class SphereObject : WorldObject
{
    public override void UpdateWorldObject(float[] data)
    {
        transform.localPosition = GetVec3(data, 0);

        Color col = GetColor24(data, 3);
        GetComponent<MeshRenderer>().material.color = col;
    }
}
