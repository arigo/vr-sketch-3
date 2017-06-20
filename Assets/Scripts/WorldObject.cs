using System.Collections;
using System.Collections.Generic;
using UnityEngine;


public abstract class WorldObject : MonoBehaviour
{
    public WorldScript.Kind kind;

    public abstract void UpdateWorldObject(float[] data);

    static public Vector3 GetVec3(float[] data, int index)
    {
        return new Vector3(data[index], data[index + 1], data[index + 2]);
    }

    static public Color GetColor24(float[] data, int index)
    {
        /* Note: only for alpha-less colors.  A float holds only 24 bits of precision */
        uint color = (uint)data[index];
        return new Color(((color >> 16) & 0xff) / 255f,
                         ((color >> 8) & 0xff) / 255f,
                         (color & 0xff) / 255f);
    }
}
